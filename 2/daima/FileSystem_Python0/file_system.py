#!/usr/bin/env python3
import os, time, json
from datetime import datetime

class FCB:
    TYPE_FILE = 0
    TYPE_DIRECTORY = 1
    def __init__(self, name, ftype, uid, gid=100):
        self.name = name
        self.type = ftype
        self.size = 0
        self.create_time = time.time()
        self.modify_time = self.create_time
        self.access_time = self.create_time
        self.owner_uid = uid
        self.owner_gid = gid
        self.permission = 0o644 if ftype == 0 else 0o755
        self.blocks = []
        self.content = ""
        self.is_open = False
        self.open_count = 0

    def get_permission_string(self):
        perms = 'd' if self.type == self.TYPE_DIRECTORY else '-'
        mode = self.permission
        for i in range(9):
            if i % 3 == 0:
                perms += 'r' if mode & (1 << (8-i)) else '-'
            elif i % 3 == 1:
                perms += 'w' if mode & (1 << (8-i)) else '-'
            else:
                perms += 'x' if mode & (1 << (8-i)) else '-'
        return perms

    def check_permission(self, uid, gid, mask):
        if uid == self.owner_uid:
            m = (self.permission >> 6) & 0x07
        elif gid == self.owner_gid:
            m = (self.permission >> 3) & 0x07
        else:
            m = self.permission & 0x07
        return (m & mask) == mask

    def to_dict(self):
        return {'name':self.name, 'type':self.type, 'size':self.size,
                'create_time':self.create_time, 'modify_time':self.modify_time,
                'access_time':self.access_time, 'owner_uid':self.owner_uid,
                'owner_gid':self.owner_gid, 'permission':self.permission,
                'blocks':self.blocks, 'content':self.content}

    @classmethod
    def from_dict(cls, data):
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
    def __init__(self, uid, gid, username, password):
        self.uid = uid; self.gid = gid
        self.username = username; self.password = password
        self.home = f"/home/{username}"
        self.last_login = 0; self.is_logged_in = False
    def verify_password(self, password):
        return self.password == password

class FileSystem:
    def __init__(self, data_file="filesystem_data.json"):
        self.data_file = data_file
        self.root = None
        self.cwd = None
        self.cwd_path = "/"
        self.users = {}
        self.name_to_uid = {}
        self.current_user = None
        self.next_uid = 1000
        self.next_gid = 100
        self.open_files = {}
        self.fd_counter = 3
        if not self._load():
            self._init_fs()

    def _init_fs(self):
        root = FCB("/", FCB.TYPE_DIRECTORY, 0, 0)
        root.permission = 0o755
        root.content = json.dumps([])
        self.root = root
        self.cwd = root
        self.cwd_path = "/"
        self.register_user("admin", "admin123")
        self.register_user("guest", "guest123")
        self.mkdir("/home")
        self.mkdir("/home/admin")
        self.mkdir("/home/guest")
        self.mkdir("/tmp")
        self.create_file("/home/admin/README.txt")
        fd = self.open_file("/home/admin/README.txt")
        if fd >= 0:
            self.write_file(fd, "欢迎使用文件系统！\n默认账号: admin/admin123")
            self.close_file(fd)
        self._save()

    def _resolve(self, path):
        if not path: return self.cwd_path
        if path.startswith('/'): return path
        if self.cwd_path == '/': return '/' + path
        return self.cwd_path + '/' + path

    def _split_path(self, path):
        abs_path = self._resolve(path)
        if abs_path == '/': return None, None
        parts = abs_path.strip('/').split('/')
        if len(parts) == 1: return '/', parts[0]
        return '/' + '/'.join(parts[:-1]), parts[-1]

    def _find_fcb(self, path):
        abs_path = self._resolve(path)
        if abs_path == '/': return self.root
        parts = abs_path.strip('/').split('/')
        cur = self.root
        for p in parts:
            found = None
            for e in json.loads(cur.content):
                if e['name'] == p:
                    found = FCB.from_dict(e); break
            if not found: return None
            cur = found
        return cur

    def _get_dir_entries(self, dir_fcb):
        if not dir_fcb or dir_fcb.type != FCB.TYPE_DIRECTORY: return []
        try: return json.loads(dir_fcb.content) if dir_fcb.content else []
        except: return []

    def _set_dir_entries(self, dir_fcb, entries):
        dir_fcb.content = json.dumps(entries)
        dir_fcb.size = len(dir_fcb.content)
        dir_fcb.modify_time = time.time()

    def _add_entry(self, dir_fcb, fcb):
        entries = self._get_dir_entries(dir_fcb)
        entries.append(fcb.to_dict())
        self._set_dir_entries(dir_fcb, entries)

    def _remove_entry(self, dir_fcb, name):
        entries = self._get_dir_entries(dir_fcb)
        entries = [e for e in entries if e['name'] != name]
        self._set_dir_entries(dir_fcb, entries)

    # ---------- 用户 ----------
    def register_user(self, username, password):
        if username in self.name_to_uid or len(username)<3 or len(password)<6: return False
        uid, gid = self.next_uid, self.next_gid
        self.next_uid += 1; self.next_gid += 1
        user = User(uid, gid, username, password)
        self.users[uid] = user
        self.name_to_uid[username] = uid
        self.mkdir(f"/home/{username}")
        self._save()
        return True

    def login_user(self, username, password):
        if username not in self.name_to_uid: return False
        user = self.users[self.name_to_uid[username]]
        if user.verify_password(password):
            self.current_user = user
            user.is_logged_in = True
            user.last_login = time.time()
            self.cd(f"/home/{username}")
            self._save()
            return True
        return False

    def logout_user(self):
        if self.current_user: self.current_user.is_logged_in = False
        self.current_user = None
        self.cd("/")
        self._save()

    def get_current_user(self): return self.current_user
    def is_user_logged_in(self): return self.current_user is not None
    def get_current_username(self): return self.current_user.username if self.current_user else ""
    def get_all_users(self): return list(self.users.values())

    # ---------- 目录 ----------
    def mkdir(self, path):
        if not self.is_user_logged_in(): return False
        parent_path, name = self._split_path(path)
        if not name: return False
        parent = self._find_fcb(parent_path)
        if not parent or parent.type != FCB.TYPE_DIRECTORY: return False
        if self._find_fcb(path): return False
        fcb = FCB(name, FCB.TYPE_DIRECTORY, self.current_user.uid, self.current_user.gid)
        fcb.permission = 0o755
        fcb.content = json.dumps([])
        self._add_entry(parent, fcb)
        self._save()
        return True

    def rmdir(self, path):
        if not self.is_user_logged_in(): return False
        abs_path = self._resolve(path)
        if abs_path in ('/', '/home'): return False
        parent_path, name = self._split_path(abs_path)
        parent = self._find_fcb(parent_path)
        if not parent: return False
        target = self._find_fcb(abs_path)
        if not target or target.type != FCB.TYPE_DIRECTORY: return False
        if self._get_dir_entries(target): return False
        self._remove_entry(parent, name)
        self._save()
        return True

    def cd(self, path):
        abs_path = self._resolve(path)
        if abs_path == '/':
            self.cwd_path = '/'; self.cwd = self.root; return True
        target = self._find_fcb(abs_path)
        if not target or target.type != FCB.TYPE_DIRECTORY: return False
        self.cwd_path = abs_path; self.cwd = target; return True

    def ls(self): return self.list_directory(self.cwd_path)

    def list_directory(self, path):
        fcb = self._find_fcb(self._resolve(path))
        if not fcb or fcb.type != FCB.TYPE_DIRECTORY: return []
        result = []
        for e in self._get_dir_entries(fcb):
            f = FCB.from_dict(e)
            line = f.get_permission_string() + " "
            line += str(f.size) + " "
            line += datetime.fromtimestamp(f.modify_time).strftime("%Y-%m-%d %H:%M:%S") + " "
            line += f.name
            if f.type == FCB.TYPE_DIRECTORY: line += "/"
            result.append(line)
        return result

    def get_current_path(self): return self.cwd_path

    # ---------- 文件 ----------
    def create_file(self, path):
        if not self.is_user_logged_in(): return False
        if self._find_fcb(path): return False
        parent_path, name = self._split_path(path)
        parent = self._find_fcb(parent_path)
        if not parent or parent.type != FCB.TYPE_DIRECTORY: return False
        fcb = FCB(name, FCB.TYPE_FILE, self.current_user.uid, self.current_user.gid)
        fcb.permission = 0o644
        fcb.content = ""
        self._add_entry(parent, fcb)
        self._save()
        return True

    def open_file(self, path):
        if not self.is_user_logged_in(): return -1
        target = self._find_fcb(path)
        if not target or target.type != FCB.TYPE_FILE: return -1
        if not target.check_permission(self.current_user.uid, self.current_user.gid, 0x01): return -1
        fd = self.fd_counter; self.fd_counter += 1
        self.open_files[fd] = (path, target)
        target.is_open = True; target.open_count += 1
        return fd

    def close_file(self, fd):
        if fd not in self.open_files: return False
        path, fcb = self.open_files[fd]
        fcb.open_count -= 1
        if fcb.open_count <= 0: fcb.is_open = False
        del self.open_files[fd]
        self._save()
        return True

    def read_file(self, fd):
        if fd not in self.open_files: return ""
        path, fcb = self.open_files[fd]
        if not fcb.check_permission(self.current_user.uid, self.current_user.gid, 0x01): return ""
        fcb.access_time = time.time()
        return fcb.content

    def write_file(self, fd, content, append=False):
        if fd not in self.open_files: return False
        path, fcb = self.open_files[fd]
        if not fcb.check_permission(self.current_user.uid, self.current_user.gid, 0x02): return False
        if append: fcb.content += content
        else: fcb.content = content
        fcb.size = len(fcb.content)
        fcb.modify_time = time.time()
        self._save()
        return True

    def delete_file(self, path):
        if not self.is_user_logged_in(): return False
        target = self._find_fcb(path)
        if not target or target.type != FCB.TYPE_FILE: return False
        parent_path, name = self._split_path(path)
        parent = self._find_fcb(parent_path)
        if not parent: return False
        to_del = [fd for fd, (p, f) in self.open_files.items() if p == path]
        for fd in to_del: del self.open_files[fd]
        self._remove_entry(parent, name)
        self._save()
        return True

    def search_file(self, filename):
        result = []
        def walk(fcb, base):
            for e in self._get_dir_entries(fcb):
                if e['name'] == filename:
                    result.append(base + '/' + e['name'] if base != '/' else '/' + e['name'])
                if e['type'] == FCB.TYPE_DIRECTORY:
                    walk(FCB.from_dict(e), base + '/' + e['name'] if base != '/' else '/' + e['name'])
        walk(self.root, "")
        return '\n'.join(result) if result else "文件未找到"

    def chmod(self, path, mode):
        if not self.is_user_logged_in(): return False
        target = self._find_fcb(path)
        if not target or target.owner_uid != self.current_user.uid: return False
        target.permission = mode
        self._save()
        return True

    def get_file_info(self, path):
        target = self._find_fcb(path)
        if not target: return "文件或目录不存在"
        return f"名称: {target.name}\n类型: {'目录' if target.type==FCB.TYPE_DIRECTORY else '文件'}\n大小: {target.size} 字节\n创建: {datetime.fromtimestamp(target.create_time).strftime('%Y-%m-%d %H:%M:%S')}\n修改: {datetime.fromtimestamp(target.modify_time).strftime('%Y-%m-%d %H:%M:%S')}\n权限: {target.get_permission_string()}\n所有者: {target.owner_uid}"

    def get_system_info(self):
        total_files = total_dirs = 0
        def count(fcb):
            nonlocal total_files, total_dirs
            if fcb.type == FCB.TYPE_FILE: total_files += 1
            else:
                total_dirs += 1
                for e in self._get_dir_entries(fcb):
                    count(FCB.from_dict(e))
        count(self.root)
        return f"总文件: {total_files}\n总目录: {total_dirs}\n用户: {self.get_current_username() or '未登录'}\n路径: {self.cwd_path}"

    # ---------- 持久化 ----------
    def _save(self):
        try:
            data = {
                'root': self.root.to_dict() if self.root else None,
                'cwd_path': self.cwd_path,
                'users': {uid: {'uid':u.uid,'gid':u.gid,'username':u.username,'password':u.password,'home':u.home,'last_login':u.last_login} for uid,u in self.users.items()},
                'name_to_uid': self.name_to_uid,
                'next_uid': self.next_uid,
                'next_gid': self.next_gid
            }
            with open(self.data_file, 'w') as f: json.dump(data, f, indent=2)
        except: pass

    def _load(self):
        try:
            if not os.path.exists(self.data_file): return False
            with open(self.data_file, 'r') as f: data = json.load(f)
            if data.get('root'): self.root = FCB.from_dict(data['root']); self.cwd = self.root; self.cwd_path = data.get('cwd_path','/')
            self.users = {}
            for uid, ud in data.get('users',{}).items():
                u = User(ud['uid'], ud['gid'], ud['username'], ud['password'])
                u.home = ud['home']; u.last_login = ud['last_login']
                self.users[int(uid)] = u
            self.name_to_uid = data.get('name_to_uid', {})
            self.next_uid = data.get('next_uid', 1000)
            self.next_gid = data.get('next_gid', 100)
            return True
        except: return False
