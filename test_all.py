#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""综合测试脚本 - 测试SteamHosts_Updater.py的功能和参数"""

import unittest
import tempfile
import shutil
import subprocess
import sys
import platform
from pathlib import Path
import yaml


class TestSteamHostsUpdater(unittest.TestCase):
    """测试SteamHosts_Updater.py的主功能"""

    test_dir = ""
    test_hosts_path = Path()

    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.test_hosts_path = Path(self.test_dir) / 'test_hosts'

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_help_option(self):
        """测试--help参数"""
        script_path = Path(__file__).parent / 'SteamHosts_Updater.py'
        result = subprocess.run(
            [sys.executable, str(script_path), '--help'],
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='replace'
        )
        print(f"Help exit code: {result.returncode}")
        print(f"Help stdout: {result.stdout[:200]}")
        print(f"Help stderr: {result.stderr[:200]}")
        self.assertEqual(result.returncode, 0, f"Exit code: {result.returncode}, stderr: {result.stderr}")
        self.assertIn('使用方法', result.stdout)
        self.assertIn('--output', result.stdout)
        self.assertIn('--log', result.stdout)
        self.assertIn('--init-config', result.stdout)

    def test_output_option(self):
        """测试--output参数"""
        script_path = Path(__file__).parent / 'SteamHosts_Updater.py'
        result = subprocess.run(
            [sys.executable, str(script_path), '-o', str(self.test_hosts_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        # 检查是否生成了hosts文件
        self.assertTrue(self.test_hosts_path.exists())

        # 验证文件内容
        with open(self.test_hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('Steam Hosts - 由程序自动生成', content)

    def test_log_option(self):
        """测试--log参数生成日志文件"""
        script_path = Path(__file__).parent / 'SteamHosts_Updater.py'
        result = subprocess.run(
            [sys.executable, str(script_path), '-o', str(self.test_hosts_path), '--log'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=self.test_dir
        )

        # 检查是否生成了日志文件
        log_files = list(Path(self.test_dir).glob('steam_hosts_updater_*.log'))
        self.assertGreater(len(log_files), 0, "应该生成至少一个日志文件")

        # 验证日志文件名格式（精确到秒）
        log_file = log_files[0]
        self.assertRegex(log_file.name, r'steam_hosts_updater_\d{8}_\d{6}\.log')

    def test_init_config_option(self):
        """测试--init-config参数"""
        config_path = Path(self.test_dir) / 'config.yaml'
        script_path = Path(__file__).parent / 'SteamHosts_Updater.py'

        result = subprocess.run(
            [sys.executable, str(script_path), '--init-config'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=self.test_dir
        )

        self.assertEqual(result.returncode, 0)
        self.assertTrue(config_path.exists(), "应该生成config.yaml文件")

        # 验证配置文件内容
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            self.assertIn('steam_domains', config)
            self.assertIn('dns', config)
            self.assertIn('output', config)


class TestConfigGeneration(unittest.TestCase):
    """测试配置文件生成功能"""

    test_dir = ""

    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_config_with_custom_domains(self):
        """测试自定义域名配置"""
        config_path = Path(self.test_dir) / 'config.yaml'
        script_path = Path(__file__).parent / 'SteamHosts_Updater.py'

        # 生成配置文件
        result = subprocess.run(
            [sys.executable, str(script_path), '--init-config'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=self.test_dir
        )
        self.assertEqual(result.returncode, 0)

        # 修改配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 添加自定义域名
        config['steam_domains'] = ['example.com', 'test.com']
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)

        # 使用配置文件生成hosts
        output_hosts = Path(self.test_dir) / 'output_hosts'
        result = subprocess.run(
            [sys.executable, str(script_path), '-o', str(output_hosts)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=self.test_dir
        )

        self.assertTrue(output_hosts.exists())


class TestParameterCombinations(unittest.TestCase):
    """测试参数组合"""

    test_dir = ""

    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_output_with_log(self):
        """测试-o和--log参数组合"""
        output_file = Path(self.test_dir) / 'test_hosts'
        script_path = Path(__file__).parent / 'SteamHosts_Updater.py'
        result = subprocess.run(
            [sys.executable, str(script_path), '-o', str(output_file), '--log'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=self.test_dir,
            encoding='utf-8',
            errors='replace'
        )
        print(f"Output file exists: {output_file.exists()}")
        print(f"Exit code: {result.returncode}")
        print(f"Stderr: {result.stderr}")

        self.assertTrue(output_file.exists())
        log_files = list(Path(self.test_dir).glob('steam_hosts_updater_*.log'))
        self.assertGreater(len(log_files), 0)

    def test_init_config_with_log(self):
        """测试--init-config和--log参数组合"""
        script_path = Path(__file__).parent / 'SteamHosts_Updater.py'
        result = subprocess.run(
            [sys.executable, str(script_path), '--init-config', '--log'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=self.test_dir,
            encoding='utf-8',
            errors='replace'
        )
        print(f"Exit code: {result.returncode}")
        print(f"Config file exists: {(Path(self.test_dir) / 'config.yaml').exists()}")
        print(f"Stderr: {result.stderr}")

        self.assertEqual(result.returncode, 0)
        self.assertTrue((Path(self.test_dir) / 'config.yaml').exists())
        log_files = list(Path(self.test_dir).glob('steam_hosts_updater_*.log'))
        self.assertGreater(len(log_files), 0)


class TestLogFilenameFormat(unittest.TestCase):
    """测试日志文件命名格式"""

    test_dir = ""

    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_main_updater_log_format(self):
        """测试主程序的日志文件命名格式"""
        script_path = Path(__file__).parent / 'SteamHosts_Updater.py'
        result = subprocess.run(
            [sys.executable, str(script_path), '-o', 'test_hosts', '--log'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=self.test_dir
        )

        log_files = list(Path(self.test_dir).glob('steam_hosts_updater_*.log'))
        self.assertGreater(len(log_files), 0)

        # 验证格式：steam_hosts_updater_YYYYMMDD_HHMMSS.log
        for log_file in log_files:
            self.assertRegex(
                log_file.name,
                r'^steam_hosts_updater_\d{8}_\d{6}\.log$',
                f"日志文件名格式不正确: {log_file.name}"
            )


def run_tests():
    """运行所有测试"""
    # 修复Windows控制台编码问题
    if platform.system() == 'Windows':
        import io
        import sys
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestSteamHostsUpdater))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestParameterCombinations))
    suite.addTests(loader.loadTestsFromTestCase(TestLogFilenameFormat))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试结果摘要
    print("\n" + "=" * 70)
    print("测试结果摘要")
    print("=" * 70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功数: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print("=" * 70)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit(run_tests())
