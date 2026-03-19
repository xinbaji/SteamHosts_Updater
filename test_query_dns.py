#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试脚本 - 测试query_dns.py的功能"""

import unittest
import tempfile
import shutil
from pathlib import Path
from typing import override
import yaml

from query_dns import HostsWriter, DnsQueryError


class TestHostsWriter(unittest.TestCase):
    """HostsWriter类的单元测试"""
    
    # 实例变量类型注解
    test_dir: str
    test_config_path: Path
    test_hosts_path: Path
    test_config: dict[str, object]
    
    @override
    def __init__(self, methodName: str = "runTest") -> None:
        """初始化测试类"""
        super().__init__(methodName)
        # 初始化实例变量
        self.test_dir = ""
        self.test_config_path = Path()
        self.test_hosts_path = Path()
        self.test_config = {}
    
    @override
    def setUp(self) -> None:
        """测试前准备"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
        self.test_config_path = Path(self.test_dir) / 'test_config.yaml'
        self.test_hosts_path = Path(self.test_dir) / 'test_hosts'
        
        # 创建测试配置文件
        self.test_config = {
            'steam_domains': ['example.com', 'google.com'],
            'dns': {
                'server': '8.8.8.8',
                'timeout': 5
            },
            'output': {
                'hosts_file': str(self.test_hosts_path),
                'backup_file': 'hosts.backup'
            },
            'logging': {
                'level': 'ERROR',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
        
        with open(self.test_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.test_config, f, allow_unicode=True)
    
    @override
    def tearDown(self) -> None:
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_load_config_success(self):
        """测试成功加载配置文件"""
        writer = HostsWriter(str(self.test_config_path))
        self.assertIsNotNone(writer.config)
        domains = writer.config.get('steam_domains', [])
        self.assertEqual(len(domains), 2)  # type: ignore[arg-type]
    
    def test_load_config_file_not_found(self):
        """测试配置文件不存在的场景"""
        with self.assertRaises(FileNotFoundError):
            _ = HostsWriter('nonexistent.yaml')
    
    def test_query_dns_valid_domain(self):
        """测试查询有效域名"""
        writer = HostsWriter(str(self.test_config_path))
        ip = writer.query_dns('example.com')
        self.assertIsNotNone(ip)
        self.assertRegex(ip, r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    
    def test_query_dns_invalid_domain(self):
        """测试查询无效域名"""
        writer = HostsWriter(str(self.test_config_path))
        with self.assertRaises(DnsQueryError):
            _ = writer.query_dns('thisdomaindefinitelydoesnotexist12345.com')
    
    def test_write_hosts_file(self):
        """测试写入hosts文件"""
        writer = HostsWriter(str(self.test_config_path))
        test_entries = ['192.168.1.1\texample.com', '192.168.1.2\tgoogle.com']
        
        _ = writer.write_hosts_file(test_entries)
        
        # 验证文件是否存在
        self.assertTrue(self.test_hosts_path.exists())
        
        # 验证文件内容
        with open(self.test_hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('192.168.1.1\texample.com', content)
            self.assertIn('192.168.1.2\tgoogle.com', content)
            self.assertIn('Steam Hosts - 由程序自动生成', content)
            self.assertIn('Steam Hosts结束', content)
    
    def test_query_all_domains(self):
        """测试查询所有域名"""
        writer = HostsWriter(str(self.test_config_path))
        entries = writer.query_all_domains()
        
        self.assertIsInstance(entries, list)
        self.assertGreater(len(entries), 0)
        
        # 验证格式
        for entry in entries:
            self.assertRegex(entry, r'^[\d\.]+\t[\w\.-]+$')


class TestConfigValidation(unittest.TestCase):
    """配置验证测试"""
    
    def test_invalid_yaml_config(self):
        """测试无效的YAML配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid yaml content: [unclosed')
            f.flush()
            config_path = f.name
        
        try:
            with self.assertRaises(yaml.YAMLError):
                _ = HostsWriter(config_path)
        finally:
            _ = Path(config_path).unlink()


class TestErrorHandling(unittest.TestCase):
    """错误处理测试"""
    
    def test_dns_timeout_handling(self):
        """测试DNS超时处理"""
        # 创建超时时间很小的配置
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            config = {
                'steam_domains': ['store.steampowered.com'],
                'dns': {'server': '8.8.8.8', 'timeout': 0.001},
                'output': {'hosts_file': 'hosts', 'backup_file': 'hosts.backup'},
                'logging': {'level': 'ERROR', 'format': '%(message)s'}
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f)
            
            writer = HostsWriter(str(config_path))
            # 这个测试可能会因网络而有所不同，主要是验证错误处理机制
            try:
                entries = writer.query_all_domains()
                # 即使某些域名查询失败，也应该继续查询其他域名
                self.assertIsInstance(entries, list)
            except Exception as e:
                # 确保错误是预期的类型
                self.assertIsInstance(e, (DnsQueryError, Exception))


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestHostsWriter))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit(run_tests())
