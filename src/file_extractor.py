#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件解压器
支持解压多种格式的压缩文件，包括密码保护的压缩包
支持从YAML配置文件管理解压参数和密码
"""

import sys
import logging
import yaml
import zipfile
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ArchiveInfo:
    """压缩包信息类"""
    filename: str
    date_str: str  # 8位年月日，如20250502
    post_id: str   # 密码所在贴编号，如5399305
    floor_number: str  # 密码所在楼，如2696
    author_id: str  # 该楼发布者账号，如26893D
    encryption_method: str  # 加密方式，如sha256
    
    @property
    def date(self) -> datetime:
        """将日期字符串转换为datetime对象"""
        return datetime.strptime(self.date_str, "%Y%m%d")
    
    @property
    def forum_url(self) -> str:
        """生成论坛URL"""
        return f"https://cc98.org/{self.post_id}/"
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'filename': self.filename,
            'date_str': self.date_str,
            'date_formatted': self.date.strftime("%Y-%m-%d"),
            'post_id': self.post_id,
            'floor_number': self.floor_number,
            'author_id': '匿名' + self.author_id,
            'encryption_method': self.encryption_method,
            'forum_url': self.forum_url,
            'password_description': f"{self.forum_url} 中 {self.floor_number}楼 匿名{self.author_id} 发表内容的{self.encryption_method}哈希"
        }


class FileExtractor:
    """文件解压器类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化解压器
        
        Args:
            config_path: 配置文件路径，默认为 ../config/extract_config.yaml
        """
        if config_path is None:
            # 获取当前文件的目录，然后找到config文件夹
            current_dir = Path(__file__).parent
            config_path = str(current_dir.parent / "config" / "extract_config.yaml")
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict:
        """加载YAML配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logging.info(f"成功加载配置文件: {self.config_path}")
                return config
        except FileNotFoundError:
            logging.error(f"配置文件未找到: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logging.error(f"配置文件格式错误: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_format = log_config.get('log_format', '%(asctime)s - %(levelname)s - %(message)s')
        log_file = log_config.get('log_file', 'logs/extract.log')
        
        # 创建日志目录
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def parse_archive_filename(self, filename: str) -> Optional[ArchiveInfo]:
        """
        解析压缩包文件名，提取相关信息
        
        命名规则：chalaoshi_csv+8位年月日+_密码所在贴编号_密码所在楼_该楼发布者账号_加密方式.zip
        例如：chalaoshi_csv20250502_5399305_2696_26893D_sha256.zip
        
        Args:
            filename: 压缩包文件名
            
        Returns:
            ArchiveInfo: 解析后的信息，如果解析失败返回None
        """
        # 定义正则表达式模式
        pattern = r'^chalaoshi_csv(\d{8})_(\d+)_(\d+)_([^_]+)_([^.]+)\.zip$'
        
        match = re.match(pattern, filename)
        if not match:
            logging.warning(f"压缩包文件名格式不符合规范: {filename}")
            return None
        
        date_str, post_id, floor_number, author_id, encryption_method = match.groups()
        
        # 验证日期格式
        try:
            datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            logging.warning(f"压缩包文件名中的日期格式无效: {date_str}")
            return None
        
        archive_info = ArchiveInfo(
            filename=filename,
            date_str=date_str,
            post_id=post_id,
            floor_number=floor_number,
            author_id=author_id,
            encryption_method=encryption_method
        )
        
        logging.info(f"成功解析压缩包文件名: {filename}")
        logging.debug(f"解析结果: {archive_info}")
        
        return archive_info
    
    def save_archive_info(self, archive_info: ArchiveInfo, output_path: Optional[str] = None) -> bool:
        """
        保存压缩包信息到JSON文件
        
        Args:
            archive_info: 压缩包信息
            output_path: 输出文件路径，如果为None则使用默认路径
            
        Returns:
            bool: 保存是否成功
        """
        if output_path is None:
            # 默认保存到 logs/archive_info.json
            output_path = "logs/archive_info.json"
        
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 读取现有数据
            existing_data = []
            if output_path_obj.exists():
                try:
                    with open(output_path_obj, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    logging.warning(f"无法读取现有的信息文件，将创建新文件: {output_path}")
                    existing_data = []
            
            # 检查是否已存在相同文件名的记录
            filename = archive_info.filename
            existing_record = None
            for i, record in enumerate(existing_data):
                if record.get('filename') == filename:
                    existing_record = i
                    break
            
            # 准备新记录
            new_record = archive_info.to_dict()
            new_record['updated_at'] = datetime.now().isoformat()
            
            if existing_record is not None:
                # 更新现有记录
                existing_data[existing_record] = new_record
                logging.info(f"更新了压缩包信息: {filename}")
            else:
                # 添加新记录
                existing_data.append(new_record)
                logging.info(f"添加了压缩包信息: {filename}")
            
            # 保存到文件
            with open(output_path_obj, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"压缩包信息已保存到: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"保存压缩包信息失败: {e}")
            return False
    
    def _get_passwords_for_file(self, archive_path: str) -> List[str]:
        """获取指定文件的密码列表"""
        passwords_config = self.config.get('passwords', {})
        
        # 获取文件名
        filename = Path(archive_path).name
        
        # 首先尝试文件特定的密码
        file_passwords = passwords_config.get('file_passwords', {})
        password_configs = file_passwords.get(filename, [])
        
        passwords = []
        for pwd_config in password_configs:
            if isinstance(pwd_config, str):
                # 向后兼容：直接字符串密码
                passwords.append(pwd_config)
            elif isinstance(pwd_config, dict):
                # 新格式：包含类型和内容
                content = pwd_config.get('content', '')
                pwd_type = pwd_config.get('type', 'hash')
                
                if pwd_type == 'raw':
                    # 原始内容，需要转换为SHA256
                    sha256_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                    passwords.append(sha256_hash)
                    logging.debug(f"将原始内容转换为SHA256哈希")
                else:
                    # 已经是哈希值或其他格式，直接使用
                    passwords.append(content)
        
        # 然后添加默认密码
        default_passwords = passwords_config.get('default_passwords', [])
        
        # 合并密码列表，去重但保持顺序
        all_passwords = []
        for pwd in passwords + default_passwords:
            if pwd not in all_passwords:
                all_passwords.append(pwd)
        
        return all_passwords
    
    def _is_supported_format(self, file_path: str) -> bool:
        """检查文件格式是否被支持"""
        extract_config = self.config.get('extract', {})
        supported_formats = extract_config.get('supported_formats', [])
        
        file_path_obj = Path(file_path)
        
        # 检查单个扩展名
        if file_path_obj.suffix.lower() in supported_formats:
            return True
        
        # 检查复合扩展名（如 .tar.gz）
        if len(file_path_obj.suffixes) >= 2:
            compound_suffix = ''.join(file_path_obj.suffixes[-2:]).lower()
            if compound_suffix in supported_formats:
                return True
        
        return False
    
    def _try_extract_with_password(self, archive_path: str, extract_dir: str, password: str) -> bool:
        """尝试使用指定密码解压ZIP文件"""
        archive_path_obj = Path(archive_path)
        file_extension = archive_path_obj.suffix.lower()
        
        try:
            if file_extension == '.zip':
                return self._extract_zip(archive_path_obj, extract_dir, password)
            else:
                logging.error(f"不支持的文件格式: {file_extension}，仅支持ZIP格式")
                return False
        except Exception as e:
            logging.debug(f"使用密码 '{password}' 解压失败: {e}")
            return False
    
    def _extract_zip(self, archive_path: Path, extract_dir: str, password: str) -> bool:
        """解压ZIP文件"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # 如果有密码，设置密码
                if password:
                    zip_ref.setpassword(password.encode('utf-8'))
                
                # 测试密码是否正确
                zip_ref.testzip()
                
                # 解压所有文件
                zip_ref.extractall(extract_dir)
                
            logging.info(f"ZIP文件解压成功: {archive_path}")
            return True
            
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as e:
            logging.debug(f"ZIP解压失败: {e}")
            return False
    
    def extract_file(self, archive_path: str, extract_dir: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        解压单个文件
        
        Args:
            archive_path: 压缩文件路径
            extract_dir: 解压目录，如果为None则使用默认目录
            password: 密码，如果为None则尝试配置中的密码列表
        
        Returns:
            bool: 解压是否成功
        """
        archive_path_obj = Path(archive_path)
        
        # 检查文件是否存在
        if not archive_path_obj.exists():
            logging.error(f"压缩文件不存在: {archive_path_obj}")
            return False
        
        # 检查文件格式是否支持
        if not self._is_supported_format(str(archive_path_obj)):
            logging.error(f"不支持的文件格式: {archive_path_obj}")
            return False
        
        # 解析压缩包文件名信息
        filename = archive_path_obj.name
        archive_info = self.parse_archive_filename(filename)
        if archive_info:
            # 保存压缩包信息
            self.save_archive_info(archive_info)
        
        # 设置解压目录
        extract_config = self.config.get('extract', {})
        if extract_dir is None:
            extract_dir = extract_config.get('default_extract_dir', 'extracted')
        
        # 确保 extract_dir 不为 None
        if extract_dir is None:
            extract_dir = 'extracted'
        
        # 创建解压目录
        extract_path = Path(extract_dir)
        extract_path.mkdir(parents=True, exist_ok=True)
        
        # 检查是否覆盖已存在的文件
        overwrite_existing = extract_config.get('overwrite_existing', False)
        if extract_path.exists() and any(extract_path.iterdir()) and not overwrite_existing:
            logging.warning(f"解压目录不为空且未设置覆盖: {extract_path}")
        
        # 获取密码列表
        if password is not None:
            passwords_to_try = [password]
        else:
            passwords_to_try = self._get_passwords_for_file(str(archive_path_obj))
        
        # 尝试解压
        logging.info(f"开始解压: {archive_path_obj} -> {extract_dir}")
        
        for pwd in passwords_to_try:
            logging.debug(f"尝试密码: {'空密码' if pwd == '' else '***'}")
            
            if self._try_extract_with_password(str(archive_path_obj), str(extract_dir), pwd):
                if pwd:
                    logging.info(f"解压成功，使用密码: ***")
                else:
                    logging.info(f"解压成功，无需密码")
                
                # 如果解压成功且有压缩包信息，更新信息为已解压
                if archive_info:
                    archive_info_dict = archive_info.to_dict()
                    archive_info_dict['extracted'] = True
                    archive_info_dict['extract_dir'] = str(extract_dir)
                    archive_info_dict['extraction_time'] = datetime.now().isoformat()
                    
                    # 重新保存包含解压状态的信息
                    self._save_archive_info_dict(archive_info_dict)
                
                return True
        
        logging.error(f"解压失败，所有密码都无效: {archive_path_obj}")
        return False
    
    def _save_archive_info_dict(self, archive_info_dict: Dict) -> bool:
        """
        保存压缩包信息字典到JSON文件（内部方法）
        
        Args:
            archive_info_dict: 压缩包信息字典
            
        Returns:
            bool: 保存是否成功
        """
        output_path = "logs/archive_info.json"
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 读取现有数据
            existing_data = []
            if output_path_obj.exists():
                try:
                    with open(output_path_obj, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    existing_data = []
            
            # 查找并更新现有记录
            filename = archive_info_dict['filename']
            updated = False
            for i, record in enumerate(existing_data):
                if record.get('filename') == filename:
                    existing_data[i] = archive_info_dict
                    updated = True
                    break
            
            if not updated:
                existing_data.append(archive_info_dict)
            
            # 保存到文件
            with open(output_path_obj, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logging.error(f"保存压缩包信息失败: {e}")
            return False
    
    def extract_from_config(self) -> Dict[str, bool]:
        """
        从配置文件中读取解压任务并执行
        
        Returns:
            Dict[str, bool]: 解压结果，键为文件路径，值为是否成功
        """
        extract_tasks = self.config.get('extract_tasks', [])
        results = {}
        
        for task in extract_tasks:
            archive_path = task.get('archive_path')
            extract_dir = task.get('extract_dir')
            password = task.get('password')
            
            if not archive_path:
                logging.warning("跳过无效任务：缺少archive_path")
                continue
            
            # 如果密码为空字符串，设为None以使用默认密码列表
            if password == "":
                password = None
            
            success = self.extract_file(archive_path, extract_dir, password)
            results[archive_path] = success
        
        return results
    
    def list_archive_contents(self, archive_path: str, password: Optional[str] = None) -> Optional[List[str]]:
        """
        列出ZIP压缩文件的内容
        
        Args:
            archive_path: 压缩文件路径
            password: 密码
        
        Returns:
            Optional[List[str]]: 文件列表，失败时返回None
        """
        archive_path_obj = Path(archive_path)
        file_extension = archive_path_obj.suffix.lower()
        
        try:
            if file_extension == '.zip':
                with zipfile.ZipFile(archive_path_obj, 'r') as zip_ref:
                    if password:
                        zip_ref.setpassword(password.encode('utf-8'))
                    return zip_ref.namelist()
            else:
                logging.error(f"不支持列出内容的文件格式: {file_extension}，仅支持ZIP格式")
                return None
                
        except Exception as e:
            logging.error(f"列出压缩文件内容失败: {e}")
            return None


def main():
    """主函数，提供命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='文件解压器')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--archive', '-a', help='要解压的压缩文件路径')
    parser.add_argument('--dir', '-d', help='解压目录')
    parser.add_argument('--password', '-p', help='解压密码')
    parser.add_argument('--list', '-l', action='store_true', help='列出压缩文件内容')
    parser.add_argument('--from-config', action='store_true', help='从配置文件中读取解压任务')
    parser.add_argument('--parse-filename', action='store_true', help='仅解析压缩包文件名信息')
    parser.add_argument('--show-info', action='store_true', help='显示已保存的压缩包信息')
    parser.add_argument('--info-file', help='压缩包信息文件路径（默认为logs/archive_info.json）')
    
    args = parser.parse_args()
    
    # 创建解压器实例
    extractor = FileExtractor(args.config)
    
    if args.show_info:
        # 显示已保存的压缩包信息
        info_file = args.info_file or "logs/archive_info.json"
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                archive_data = json.load(f)
            
            print(f"已保存的压缩包信息 ({len(archive_data)} 个):")
            print("=" * 80)
            for i, info in enumerate(archive_data, 1):
                print(f"{i}. 文件名: {info.get('filename', 'N/A')}")
                print(f"   日期: {info.get('date_formatted', 'N/A')}")
                print(f"   帖子ID: {info.get('post_id', 'N/A')}")
                print(f"   楼层: {info.get('floor_number', 'N/A')}")
                print(f"   发布者: {info.get('author_id', 'N/A')}")
                print(f"   加密方式: {info.get('encryption_method', 'N/A')}")
                print(f"   论坛链接: {info.get('forum_url', 'N/A')}")
                print(f"   密码描述: {info.get('password_description', 'N/A')}")
                if info.get('extracted'):
                    print(f"   解压状态: 已解压到 {info.get('extract_dir', 'N/A')}")
                    print(f"   解压时间: {info.get('extraction_time', 'N/A')}")
                else:
                    print(f"   解压状态: 未解压")
                print("-" * 80)
        except FileNotFoundError:
            print(f"信息文件不存在: {info_file}")
        except json.JSONDecodeError:
            print(f"信息文件格式错误: {info_file}")
        except Exception as e:
            print(f"读取信息文件失败: {e}")
    elif args.from_config:
        # 从配置文件解压
        results = extractor.extract_from_config()
        success_count = sum(results.values())
        total_count = len(results)
        print(f"解压完成: {success_count}/{total_count} 个文件成功")
    elif args.archive:
        if args.parse_filename:
            # 仅解析文件名
            filename = Path(args.archive).name
            archive_info = extractor.parse_archive_filename(filename)
            if archive_info:
                print("解析结果:")
                info_dict = archive_info.to_dict()
                for key, value in info_dict.items():
                    print(f"  {key}: {value}")
                
                # 保存解析结果
                extractor.save_archive_info(archive_info)
                print("\n信息已保存到 logs/archive_info.json")
            else:
                print("文件名格式不符合规范")
                sys.exit(1)
        elif args.list:
            # 列出压缩文件内容
            contents = extractor.list_archive_contents(args.archive, args.password)
            if contents:
                print(f"压缩文件内容 ({len(contents)} 个文件):")
                for item in contents:
                    print(f"  {item}")
            else:
                print("无法列出压缩文件内容")
                sys.exit(1)
        else:
            # 解压单个文件
            success = extractor.extract_file(args.archive, args.dir, args.password)
            if success:
                print("文件解压成功")
            else:
                print("文件解压失败")
                sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
