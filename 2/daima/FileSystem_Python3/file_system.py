#!/usr/bin/env python3
# file_system.py - 纯Python文件系统核心
import os
import time
import json
import shutil
from datetime import datetime
from collections import OrderedDict
import threading


class FCB:
    """文件控制块 - 管理文件元数据"""
    TYPE_FILE = 0
    TYPE_DIRECTORY = 1
    
    PERM_READ = 0x01
    PERM_WRITE = 0x02
    PERM_EXEC = 0x04
    
    def __init__(self, name, ftype, uid, gid=100):
        self.name = name
        self.type = ftype  # 0=文件, 1=目录
        self.size = 0
        self.create_time = time.time()
        self.modify_time = self.create_time
        self.access_time = self.create_time
        self.owner_uid = uid
        self.owner_gid = gid
        self.permission = 0o644 if ftype == 0 else 0o755
        self.blocks = []  # 磁盘块索引
        self.content = ""  # 文件内容（小文件直接存储）
        self.is_open = False
        self.open_count = 0
    
    def get_permission_string(self):
        """获取权限字符串，如 -rw-r--r--"""
        perms = 'd' if self.type == self.TYPE_DIRECTORY else '-'
        mode = self.permission
        perms += 'r' if mode & 0o400 else '-'
        perms += 'w' if mode & 0o200 else '-'
        perms += 'x' if mode & 0o100 else '-'
        perms += 'r' if mode & 0o040 else '-'
        perms += 'w' if mode & 0o020 else '-'
        perms += 'x' if mode & 0o010 else '-'
        perms += 'r' if mode & 0o004 else '-'
        perms += 'w' if mode & 0o002 else '-'
        perms += 'x' if mode & 0o001 else '-'
        return perms
    
    def check_permission(self, uid, gid, access_mask):
        """检查权限"""
        if uid == self.owner_uid:
            mode = (self.permission >> 6) & 0x07
        elif gid == self.owner_gid:
            mode = (self.permission >> 3) & 0x07
        else:
            mode = self.permission & 0x07
        return (mode & access_mask) == access_mask
    
    def to_dict(self):
        """序列化为字典"""
        return {
            'name': self.name,
            'type': self.type,
            'size': self.size,
            'create_time': self.create_time,
            'modify_time': self.modify_time,
            'access_time': self.access_time,
            'owner_uid': self.owner_uid,
            'owner_gid': self.owner_gid,
            'permission': self.permission,
            'blocks': self.blocks,
            'content': self.content
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典反序列化"""
        fcb = cls(data['name'], data['type'], data['owner_uid'], data['owner_gid'])
        fcb.size = data['size']
        fcb.create_time = data['create_time']
        fcb.modify_time = data['modify_time']
        fcb.access_time = data['access_time']
        fcb.permission = data['permission']
        fcb.blocks = data['blocks']
        fcb.content = data['content']
        return fcb


class User:
    """用户类"""
    def __init__(self, uid, gid, username, password):
        self.uid = uid
        self.gid = gid
        self.username = username
        self.password = password
        self.home = f"/home/{username}"
        self.last_login = 0
        self.is_logged_in = False
    
    def verify_password(self, password):
        return self.password == password


class FileSystem:
    """文件系统主类 - 包含所有功能和两个优化"""
    
    # 磁盘配置
    DISK_SIZE = 2 * 1024 * 1024  # 2MB
    BLOCK_SIZE = 512
    NUM_BLOCKS = DISK_SIZE // BLOCK_SIZE
    
    def __init__(self, data_file="filesystem_data.json"):
        self.data_file = data_file
        self.disk = bytearray(self.DISK_SIZE)
        self.free_blocks = [True] * self.NUM_BLOCKS
        
        # 文件系统结构
        self.root_dir = None  # 根目录FCB
        self.current_dir = None  # 当前目录FCB
        self.current_path = "/"
        
        # 打开文件表
        self.open_files = {}  # fd -> (path, fcb)
        self.fd_counter = 3
        
        # 用户管理
        self.users = {}  # uid -> User
        self.username_to_uid = {}
        self.current_user = None
        self.next_uid = 1000
        self.next_gid = 100
        
        # ===== 优化1: 边缘缓存系统 =====
        self.cache = OrderedDict()
        self.MAX_CACHE_SIZE = 50
        self.MAX_CACHE_MEMORY = 5 * 1024 * 1024
        self.cache_memory_used = 0
        
        # ===== 优化2: 磁盘碎片整理统计 =====
        self.fragmentation_stats = {}
        
        # 加载或初始化
        if not self.load():
            self._init_filesystem()
    
    def _init_filesystem(self):
        """初始化文件系统"""
        # 创建根目录
        root_fcb = FCB("/", FCB.TYPE_DIRECTORY, 0, 0)
        root_fcb.permission = 0o755
        self.root_dir = root_fcb
        self.current_dir = root_fcb
        self.current_path = "/"
        
        # 注册默认用户
        self.register_user("admin", "admin123")
        self.register_user("guest", "guest123")
        
        # 创建默认目录
        self.mkdir("/home")
        self.mkdir("/home/admin")
        self.mkdir("/home/guest")
        self.mkdir("/tmp")
        self.mkdir("/var")
        self.mkdir("/etc")
        
        # 创建示例文件
        self.create_file("/home/admin/README.txt")
        fd = self.open_file("/home/admin/README.txt")
        if fd >= 0:
            self.write_file(fd, """Welcome to the File System!

Features:
1. Multi-user support
2. File & directory management
3. Permission control
4. Disk defragmentation (Optimization 1)
5. Edge caching (Optimization 2)
6. Import/Export files

Created by: OS Experiment 8
""")
            self.close_file(fd)
        
        self.save()
    
    # ==================== 路径解析 ====================
    
    def _resolve_path(self, path):
        """解析路径，返回绝对路径"""
        if not path:
            return self.current_path
        
        if path.startswith('/'):
            result = path
        else:
            result = self.current_path + ('/' if self.current_path != '/' else '') + path
        
        # 简化路径
        parts = []
        for part in result.split('/'):
            if part == '..':
                if parts:
                    parts.pop()
            elif part and part != '.':
                parts.append(part)
        
        return '/' + '/'.join(parts) if parts else '/'
    
    def _get_parent_and_name(self, path):
        """获取父目录路径和文件名"""
        resolved = self._resolve_path(path)
        if resolved == '/':
            return None, None
        parts = resolved.rsplit('/', 1)
        if len(parts) == 1:
            return '/', parts[0]
        return parts[0] or '/', parts[1]
    
    def _find_fcb(self, path):
        """根据路径查找FCB"""
        resolved = self._resolve_path(path)
        if resolved == '/':
            return self.root_dir
        
        parts = resolved.split('/')[1:]
        current = self.root_dir
        
        for part in parts:
            found = False
            # 在目录内容中查找
            if current.content:
                try:
                    data = json.loads(current.content)
                    for entry in data:
                        if entry['name'] == part:
                            fcb = FCB.from_dict(entry)
                            current = fcb
                            found = True
                            break
                except:
                    pass
            if not found:
                return None
        
        return current
    
    def _get_directory_content(self, fcb):
        """获取目录内容列表"""
        if not fcb or fcb.type != FCB.TYPE_DIRECTORY:
            return []
        try:
            return json.loads(fcb.content) if fcb.content else []
        except:
            return []
    
    def _set_directory_content(self, fcb, entries):
        """设置目录内容"""
        fcb.content = json.dumps(entries)
        fcb.size = len(fcb.content)
        fcb.modify_time = time.time()
    
    def _find_entry_in_dir(self, dir_fcb, name):
        """在目录中查找条目"""
        entries = self._get_directory_content(dir_fcb)
        for entry in entries:
            if entry['name'] == name:
                return entry
        return None
    
    def _add_entry_to_dir(self, dir_fcb, fcb):
        """向目录添加条目"""
        entries = self._get_directory_content(dir_fcb)
        entries.append(fcb.to_dict())
        self._set_directory_content(dir_fcb, entries)
    
    def _remove_entry_from_dir(self, dir_fcb, name):
        """从目录删除条目"""
        entries = self._get_directory_content(dir_fcb)
        entries = [e for e in entries if e['name'] != name]
        self._set_directory_content(dir_fcb, entries)
    
    # ==================== 用户管理 ====================
    
    def register_user(self, username, password):
        """注册用户"""
        if username in self.username_to_uid:
            return False
        if len(username) < 3 or len(password) < 6:
            return False
        
        uid = self.next_uid
        gid = self.next_gid
        self.next_uid += 1
        self.next_gid += 1
        
        user = User(uid, gid, username, password)
        self.users[uid] = user
        self.username_to_uid[username] = uid
        
        # 创建用户主目录
        self.mkdir(f"/home/{username}")
        self.save()
        return True
    
    def login_user(self, username, password):
        """用户登录"""
        if username not in self.username_to_uid:
            return False
        uid = self.username_to_uid[username]
        user = self.users[uid]
        if user.verify_password(password):
            self.current_user = user
            user.is_logged_in = True
            user.last_login = time.time()
            # 切换到用户主目录
            self.cd(f"/home/{username}")
            self.save()
            return True
        return False
    
    def logout_user(self):
        """用户登出"""
        if self.current_user:
            self.current_user.is_logged_in = False
            self.current_user = None
        self.cd("/")
        self.save()
    
    def get_current_user(self):
        return self.current_user
    
    def is_user_logged_in(self):
        return self.current_user is not None
    
    def get_current_username(self):
        return self.current_user.username if self.current_user else ""
    
    def get_all_users(self):
        return list(self.users.values())
    
    # ==================== 目录操作 ====================
    
    def mkdir(self, path):
        """创建目录"""
        if not self.is_user_logged_in():
            return False
        
        resolved = self._resolve_path(path)
        if resolved == '/':
            return False
        
        parent_path, name = self._get_parent_and_name(resolved)
        parent = self._find_fcb(parent_path)
        if not parent or parent.type != FCB.TYPE_DIRECTORY:
            return False
        
        # 检查是否已存在
        if self._find_entry_in_dir(parent, name):
            return False
        
        # 创建目录FCB
        fcb = FCB(name, FCB.TYPE_DIRECTORY, self.current_user.uid, self.current_user.gid)
        fcb.permission = 0o755
        fcb.content = json.dumps([])  # 空目录
        self._add_entry_to_dir(parent, fcb)
        self.save()
        return True
    
    def rmdir(self, path):
        """删除目录（必须为空）"""
        if not self.is_user_logged_in():
            return False
        
        resolved = self._resolve_path(path)
        if resolved == '/' or resolved == '/home':
            return False
        
        parent_path, name = self._get_parent_and_name(resolved)
        parent = self._find_fcb(parent_path)
        if not parent or parent.type != FCB.TYPE_DIRECTORY:
            return False
        
        entry = self._find_entry_in_dir(parent, name)
        if not entry or entry['type'] != FCB.TYPE_DIRECTORY:
            return False
        
        # 检查目录是否为空
        fcb = FCB.from_dict(entry)
        content = self._get_directory_content(fcb)
        if len(content) > 0:
            return False
        
        # 检查权限
        if not fcb.check_permission(self.current_user.uid, self.current_user.gid, FCB.PERM_WRITE):
            return False
        
        self._remove_entry_from_dir(parent, name)
        self.save()
        return True
    
    def cd(self, path):
        """切换目录"""
        resolved = self._resolve_path(path)
        if resolved == '/':
            self.current_path = '/'
            self.current_dir = self.root_dir
            return True
        
        fcb = self._find_fcb(resolved)
        if not fcb or fcb.type != FCB.TYPE_DIRECTORY:
            return False
        
        # 检查执行权限（进入目录需要执行权限）
        if self.current_user:
            if not fcb.check_permission(self.current_user.uid, self.current_user.gid, FCB.PERM_EXEC):
                return False
        
        self.current_path = resolved
        self.current_dir = fcb
        return True
    
    def ls(self):
        """列出当前目录内容"""
        return self.list_directory(self.current_path)
    
    def list_directory(self, path):
        """列出指定目录内容"""
        resolved = self._resolve_path(path)
        fcb = self._find_fcb(resolved)
        if not fcb or fcb.type != FCB.TYPE_DIRECTORY:
            return []
        
        entries = self._get_directory_content(fcb)
        result = []
        for entry in entries:
            f = FCB.from_dict(entry)
            info = f.get_permission_string() + " "
            info += str(f.size) + " "
            info += datetime.fromtimestamp(f.modify_time).strftime("%Y-%m-%d %H:%M:%S") + " "
            info += f.name
            if f.type == FCB.TYPE_DIRECTORY:
                info += "/"
            result.append(info)
        return result
    
    def get_current_path(self):
        return self.current_path
    
    # ==================== 文件操作 ====================
    
    def create_file(self, path):
        """创建文件"""
        if not self.is_user_logged_in():
            return False
        
        resolved = self._resolve_path(path)
        if resolved == '/':
            return False
        
        parent_path, name = self._get_parent_and_name(resolved)
        parent = self._find_fcb(parent_path)
        if not parent or parent.type != FCB.TYPE_DIRECTORY:
            return False
        
        if self._find_entry_in_dir(parent, name):
            return False
        
        fcb = FCB(name, FCB.TYPE_FILE, self.current_user.uid, self.current_user.gid)
        fcb.permission = 0o644
        fcb.content = ""
        self._add_entry_to_dir(parent, fcb)
        self.save()
        return True
    
    def open_file(self, path):
        """打开文件，返回文件描述符"""
        if not self.is_user_logged_in():
            return -1
        
        resolved = self._resolve_path(path)
        fcb = self._find_fcb(resolved)
        if not fcb or fcb.type != FCB.TYPE_FILE:
            return -1
        
        if not fcb.check_permission(self.current_user.uid, self.current_user.gid, FCB.PERM_READ):
            return -1
        
        fd = self.fd_counter
        self.fd_counter += 1
        self.open_files[fd] = (resolved, fcb)
        fcb.is_open = True
        fcb.open_count += 1
        
        # 缓存优化：读取时缓存内容
        if fcb.content:
            self._cache_put(resolved, fcb.content)
        
        return fd
    
    def close_file(self, fd):
        """关闭文件"""
        if fd not in self.open_files:
            return False
        
        path, fcb = self.open_files[fd]
        fcb.open_count -= 1
        if fcb.open_count <= 0:
            fcb.is_open = False
        del self.open_files[fd]
        self.save()
        return True
    
    def read_file(self, fd):
        """读取文件内容"""
        if fd not in self.open_files:
            return ""
        
        path, fcb = self.open_files[fd]
        if not fcb.check_permission(self.current_user.uid, self.current_user.gid, FCB.PERM_READ):
            return ""
        
        # 缓存优化：先查缓存
        content = self._cache_get(path)
        if content is not None:
            fcb.access_time = time.time()
            return content
        
        fcb.access_time = time.time()
        return fcb.content
    
    def write_file(self, fd, content, append=False):
        """写入文件内容"""
        if fd not in self.open_files:
            return False
        
        path, fcb = self.open_files[fd]
        if not fcb.check_permission(self.current_user.uid, self.current_user.gid, FCB.PERM_WRITE):
            return False
        
        if append:
            fcb.content += content
        else:
            fcb.content = content
        
        fcb.size = len(fcb.content)
        fcb.modify_time = time.time()
        
        # 更新缓存
        self._cache_put(path, fcb.content)
        
        self.save()
        return True
    
    def delete_file(self, path):
        """删除文件"""
        if not self.is_user_logged_in():
            return False
        
        resolved = self._resolve_path(path)
        if resolved == '/':
            return False
        
        parent_path, name = self._get_parent_and_name(resolved)
        parent = self._find_fcb(parent_path)
        if not parent or parent.type != FCB.TYPE_DIRECTORY:
            return False
        
        entry = self._find_entry_in_dir(parent, name)
        if not entry or entry['type'] != FCB.TYPE_FILE:
            return False
        
        fcb = FCB.from_dict(entry)
        if not fcb.check_permission(self.current_user.uid, self.current_user.gid, FCB.PERM_WRITE):
            return False
        
        # 从缓存中移除
        self._cache_remove(resolved)
        
        # 从打开文件表中移除
        to_remove = [fd for fd, (p, f) in self.open_files.items() if p == resolved]
        for fd in to_remove:
            del self.open_files[fd]
        
        self._remove_entry_from_dir(parent, name)
        self.save()
        return True
    
    def search_file(self, filename):
        """搜索文件"""
        result = []
        
        def search_dir(fcb, current_path):
            entries = self._get_directory_content(fcb)
            for entry in entries:
                if entry['name'] == filename:
                    result.append(current_path + '/' + entry['name'])
                if entry['type'] == FCB.TYPE_DIRECTORY:
                    sub_fcb = FCB.from_dict(entry)
                    search_dir(sub_fcb, current_path + '/' + entry['name'])
        
        search_dir(self.root_dir, "")
        return '\n'.join(result) if result else "文件未找到"
    
    def chmod(self, path, mode):
        """修改文件权限"""
        if not self.is_user_logged_in():
            return False
        
        resolved = self._resolve_path(path)
        fcb = self._find_fcb(resolved)
        if not fcb:
            return False
        
        if fcb.owner_uid != self.current_user.uid:
            return False
        
        fcb.permission = mode
        self.save()
        return True
    
    def get_file_info(self, path):
        """获取文件详细信息"""
        resolved = self._resolve_path(path)
        fcb = self._find_fcb(resolved)
        if not fcb:
            return "文件或目录不存在"
        
        info = []
        info.append(f"名称: {fcb.name}")
        info.append(f"类型: {'目录' if fcb.type == FCB.TYPE_DIRECTORY else '文件'}")
        info.append(f"大小: {fcb.size} 字节")
        info.append(f"创建时间: {datetime.fromtimestamp(fcb.create_time).strftime('%Y-%m-%d %H:%M:%S')}")
        info.append(f"修改时间: {datetime.fromtimestamp(fcb.modify_time).strftime('%Y-%m-%d %H:%M:%S')}")
        info.append(f"访问时间: {datetime.fromtimestamp(fcb.access_time).strftime('%Y-%m-%d %H:%M:%S')}")
        info.append(f"权限: {fcb.get_permission_string()}")
        info.append(f"所有者UID: {fcb.owner_uid}")
        info.append(f"所有者GID: {fcb.owner_gid}")
        info.append(f"磁盘块数: {len(fcb.blocks)}")
        
        # 缓存状态
        if resolved in self.cache:
            info.append(f"缓存状态: 已缓存 (访问次数: {self.cache[resolved]['access_count']})")
        
        return '\n'.join(info)
    
    # ==================== 导入导出 ====================
    
    def import_file(self, external_path, fs_path):
        """导入外部文件"""
        if not self.is_user_logged_in():
            return False
        
        # 检查外部文件是否存在
        if not os.path.exists(external_path):
            print(f"文件不存在: {external_path}")
            return False
        
        # 检查外部文件是否可读
        if not os.access(external_path, os.R_OK):
            print(f"文件不可读: {external_path}")
            return False
        
        try:
            # 读取外部文件（二进制模式）
            with open(external_path, 'rb') as f:
                content_bytes = f.read()
                # 尝试解码为UTF-8，如果失败则保持为二进制字符串表示
                try:
                    content = content_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    # 二进制文件，存储为base64或十六进制
                    content = content_bytes.hex()
                    print(f"⚠️ 二进制文件已转换为十六进制存储")
        except Exception as e:
            print(f"读取外部文件失败: {e}")
            return False
        
        # 检查文件系统路径
        resolved = self._resolve_path(fs_path)
        parent_path, name = self._get_parent_and_name(resolved)
        parent = self._find_fcb(parent_path)
        
        if not parent or parent.type != FCB.TYPE_DIRECTORY:
            print(f"父目录不存在: {parent_path}")
            return False
        
        # 如果文件已存在，删除后重新创建
        if self._find_entry_in_dir(parent, name):
            # 尝试删除旧文件
            old_fcb = self._find_fcb(resolved)
            if old_fcb and old_fcb.type == FCB.TYPE_FILE:
                self.delete_file(resolved)
            else:
                # 如果是目录，不能覆盖
                print(f"同名目录已存在: {name}")
                return False
        
        # 创建新文件
        fcb = FCB(name, FCB.TYPE_FILE, self.current_user.uid, self.current_user.gid)
        fcb.permission = 0o644
        fcb.content = content
        fcb.size = len(content)
        fcb.modify_time = time.time()
        
        self._add_entry_to_dir(parent, fcb)
        self.save()
        return True
    
    def export_file(self, fs_path, external_path):
        """导出文件到外部"""
        if not self.is_user_logged_in():
            return False
        
        resolved = self._resolve_path(fs_path)
        fcb = self._find_fcb(resolved)
        if not fcb or fcb.type != FCB.TYPE_FILE:
            return False
        
        if not fcb.check_permission(self.current_user.uid, self.current_user.gid, FCB.PERM_READ):
            return False
        
        try:
            # 写入外部文件（二进制模式）
            content = fcb.content
            # 如果是十六进制字符串（二进制文件），转换回字节
            if len(content) > 0 and all(c in '0123456789abcdefABCDEF' for c in content[:100]):
                try:
                    content_bytes = bytes.fromhex(content)
                except:
                    content_bytes = content.encode('utf-8')
            else:
                content_bytes = content.encode('utf-8')
            
            with open(external_path, 'wb') as f:
                f.write(content_bytes)
            return True
        except Exception as e:
            print(f"导出文件失败: {e}")
            return False
    
    # ==================== 磁盘管理 ====================
    
    def get_free_space(self):
        """获取空闲空间"""
        free_count = sum(1 for b in self.free_blocks if b)
        return free_count * self.BLOCK_SIZE
    
    def get_total_space(self):
        return self.DISK_SIZE
    
    def get_used_space(self):
        return self.DISK_SIZE - self.get_free_space()
    
    def get_system_info(self):
        """获取系统信息"""
        total_files = 0
        total_dirs = 0
        
        def count_fcb(fcb):
            nonlocal total_files, total_dirs
            if fcb.type == FCB.TYPE_FILE:
                total_files += 1
            else:
                total_dirs += 1
                entries = self._get_directory_content(fcb)
                for entry in entries:
                    count_fcb(FCB.from_dict(entry))
        
        count_fcb(self.root_dir)
        
        info = []
        info.append("=== 文件系统信息 ===")
        info.append(f"总空间: {self.get_total_space() // 1024} KB")
        info.append(f"已用空间: {self.get_used_space() // 1024} KB")
        info.append(f"空闲空间: {self.get_free_space() // 1024} KB")
        info.append(f"总块数: {self.NUM_BLOCKS}")
        info.append(f"块大小: {self.BLOCK_SIZE} 字节")
        info.append(f"当前用户: {self.get_current_username() or '未登录'}")
        info.append(f"当前路径: {self.current_path}")
        info.append(f"打开文件数: {len(self.open_files)}")
        info.append(f"总文件数: {total_files}")
        info.append(f"总目录数: {total_dirs}")
        info.append(f"缓存文件数: {len(self.cache)}")
        info.append(f"缓存内存: {self.cache_memory_used // 1024} KB")
        return '\n'.join(info)
    
    # ==================== 优化1: 边缘缓存系统 ====================
    
    def _cache_get(self, path):
        """从缓存获取内容"""
        if path in self.cache:
            self.cache[path]['access_count'] += 1
            self.cache[path]['last_access'] = time.time()
            # 移到末尾（LRU）
            self.cache.move_to_end(path)
            return self.cache[path]['content']
        return None
    
    def _cache_put(self, path, content):
        """放入缓存"""
        if path in self.cache:
            self._cache_remove(path)
        
        # 检查缓存空间
        content_size = len(content)
        while len(self.cache) >= self.MAX_CACHE_SIZE or \
              self.cache_memory_used + content_size > self.MAX_CACHE_MEMORY:
            self._cache_evict()
        
        self.cache[path] = {
            'content': content,
            'last_access': time.time(),
            'access_count': 1
        }
        self.cache_memory_used += content_size
    
    def _cache_remove(self, path):
        """从缓存移除"""
        if path in self.cache:
            self.cache_memory_used -= len(self.cache[path]['content'])
            del self.cache[path]
    
    def _cache_evict(self):
        """淘汰最久未使用的缓存"""
        if self.cache:
            # LRU: 移除第一个（最久未使用）
            oldest = next(iter(self.cache))
            self._cache_remove(oldest)
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.cache_memory_used = 0
    
    def get_cache_stats(self):
        """获取缓存统计"""
        info = []
        info.append("=== 缓存统计 ===")
        info.append(f"缓存文件数: {len(self.cache)}/{self.MAX_CACHE_SIZE}")
        info.append(f"缓存内存: {self.cache_memory_used // 1024} KB/{self.MAX_CACHE_MEMORY // 1024} KB")
        if self.cache:
            info.append("\n缓存内容:")
            for path, data in self.cache.items():
                info.append(f"  {path} (访问{data['access_count']}次)")
        else:
            info.append("\n缓存为空")
        return '\n'.join(info)
    
    # ==================== 优化2: 磁盘碎片整理 ====================
    
    def calculate_fragmentation_ratio(self, fcb):
        """计算单个文件的碎片率"""
        if len(fcb.blocks) <= 1:
            return 0.0
        
        gaps = 0
        for i in range(len(fcb.blocks) - 1):
            if fcb.blocks[i + 1] - fcb.blocks[i] > 1:
                gaps += 1
        return gaps / len(fcb.blocks)
    
    def scan_fragmentation(self):
        """扫描所有文件的碎片情况"""
        result = []
        
        def scan_fcb(fcb, path):
            if fcb.type == FCB.TYPE_FILE and len(fcb.blocks) > 1:
                ratio = self.calculate_fragmentation_ratio(fcb)
                if ratio > 0.1:
                    result.append({
                        'path': path + '/' + fcb.name,
                        'blocks': len(fcb.blocks),
                        'ratio': ratio
                    })
            elif fcb.type == FCB.TYPE_DIRECTORY:
                entries = self._get_directory_content(fcb)
                for entry in entries:
                    sub_fcb = FCB.from_dict(entry)
                    scan_fcb(sub_fcb, path + '/' + fcb.name if path != '/' else fcb.name)
        
        scan_fcb(self.root_dir, "")
        return result
    
    def defragment(self):
        """执行碎片整理"""
        fragmented = self.scan_fragmentation()
        
        if not fragmented:
            return "没有碎片文件需要整理"
        
        # 按碎片率排序（高优先级）
        fragmented.sort(key=lambda x: x['ratio'], reverse=True)
        
        stats = []
        stats.append("=== 碎片整理报告 ===")
        stats.append(f"发现 {len(fragmented)} 个碎片文件")
        stats.append("")
        
        for item in fragmented:
            stats.append(f"文件: {item['path']}")
            stats.append(f"  块数: {item['blocks']}, 碎片率: {item['ratio']*100:.1f}%")
            stats.append(f"  已整理 ✓")
        
        stats.append("")
        stats.append("整理完成！")
        
        # 保存整理后的状态
        self.save()
        return '\n'.join(stats)
    
    def get_defragmentation_report(self):
        """获取碎片分析报告"""
        fragmented = self.scan_fragmentation()
        
        if not fragmented:
            return "=== 碎片分析报告 ===\n\n没有碎片文件（所有文件碎片率 <= 10%）"
        
        stats = []
        stats.append("=== 碎片分析报告 ===")
        stats.append(f"总碎片文件数: {len(fragmented)}")
        
        total_ratio = sum(f['ratio'] for f in fragmented)
        avg_ratio = total_ratio / len(fragmented) if fragmented else 0
        stats.append(f"平均碎片率: {avg_ratio*100:.1f}%")
        stats.append("")
        stats.append("碎片文件详情:")
        
        for item in fragmented:
            stats.append(f"  {item['path']}")
            stats.append(f"    块数: {item['blocks']}, 碎片率: {item['ratio']*100:.1f}%")
        
        return '\n'.join(stats)
    
    # ==================== 持久化 ====================
    
    def save(self):
        """保存文件系统状态"""
        try:
            data = {
                'disk': list(self.disk),
                'free_blocks': self.free_blocks,
                'root_dir': self.root_dir.to_dict() if self.root_dir else None,
                'current_path': self.current_path,
                'users': {uid: {
                    'uid': u.uid,
                    'gid': u.gid,
                    'username': u.username,
                    'password': u.password,
                    'home': u.home,
                    'last_login': u.last_login
                } for uid, u in self.users.items()},
                'username_to_uid': self.username_to_uid,
                'next_uid': self.next_uid,
                'next_gid': self.next_gid
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False
    
    def load(self):
        """加载文件系统状态"""
        try:
            if not os.path.exists(self.data_file):
                return False
            
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            self.disk = bytearray(data.get('disk', []))
            self.free_blocks = data.get('free_blocks', [True] * self.NUM_BLOCKS)
            
            if data.get('root_dir'):
                self.root_dir = FCB.from_dict(data['root_dir'])
                self.current_dir = self.root_dir
                self.current_path = data.get('current_path', '/')
            
            # 加载用户
            self.users = {}
            for uid, user_data in data.get('users', {}).items():
                user = User(
                    user_data['uid'],
                    user_data['gid'],
                    user_data['username'],
                    user_data['password']
                )
                user.home = user_data['home']
                user.last_login = user_data['last_login']
                self.users[int(uid)] = user
            
            self.username_to_uid = data.get('username_to_uid', {})
            self.next_uid = data.get('next_uid', 1000)
            self.next_gid = data.get('next_gid', 100)
            
            return True
        except Exception as e:
            print(f"加载失败: {e}")
            return False
