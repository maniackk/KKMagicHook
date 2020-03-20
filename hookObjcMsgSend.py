import os
import re
import struct
from pathlib import Path

'''
静态库结构

1、魔数 8个字节
magic(8) = '!<arch>\n'

2、符号表头结构 80个字节
struct symtab_header {
    char        name[16];       /* 名称 */
    char        timestamp[12];  /* 库创建的时间戳 */
    char        userid[6];        /* 用户id */
    char        groupid[6];  /* 组id */
    uint64_t    mode;            /* 文件访问模式 */
    uint64_t    size;            /* 符号表占总字节大小 */
    uint32_t    endheader;        /* 头结束标志 */
    char        longname[20];   /* 符号表长名 */
};

3、符号表 4+size个字节
struct symbol_table {
    uint32_t       size;           /* 符号表占用的总字节数 */
    symbol_info syminfo[0];      /* 符号信息，它的个数是 size / sizeof(symbol_info) */
};

3、字符串表 4+size个字节
struct stringtab
{
    int size;     //字符串表的尺寸
    char strings[0];   //字符串表的内容，每个字符串以\0分隔。
};

4、目标文件头结构（跟符号表头结构一样） 80个字节

struct object_header {
    char        name[16];       /* 名称 */
    char        timestamp[12];  /* 目标文件创建的时间戳 */
    char        userid[6];        /* 用户id */
    char        groupid[6];  /* 组id */
    uint64_t    mode;            /* 文件访问模式 */
    uint64_t    size;            /* 符号表占总字节大小 */
    uint32_t    endheader;        /* 头结束标志 */
    char        longname[20];   /* 符号表长名 */
};

5、目标文件
这个可以参考我的博客：https://juejin.im/post/5d5275b251882505417927b5

.....4、5循环（如果有多个目标文件）

'''


def get_valid_staticLib_path():
    if not Path(staticLibPath).is_file():
        return False, 'invalid path, please input valid staticLib path!!!'
    output = os.popen('lipo -detailed_info '+staticLibPath).read().strip()
    if not output.endswith('architecture: arm64'):  # re.match(r'.*architecture: arm64$', output):
        return False, 'invalid staticLib or not arm64(not fat file)'
    with open(staticLibPath, 'rb') as fileobj:
        magic = fileobj.read(8)
        (magic,) = struct.unpack('8s', magic)
        magic = magic.decode('utf-8')
        if not magic == '!<arch>\n':
            return False, 'error magic, invalid staticLib.'
    return True, 'valid path!'


# 返回(name, location, size)
def resolver_object_header(offset):
    with open(staticLibPath, 'rb') as fileobj:
        fileobj.seek(offset)
        name = fileobj.read(16)
        (name,) = struct.unpack('16s', name)
        name = name.decode()
        # offset(48+offset) = offset + name(16) + timestamp(12) + userid(6) + groupid(6) + mode(8)
        fileobj.seek(48+offset)
        size = fileobj.read(8)
        (size,) = struct.unpack('8s', size)
        size = int(size.decode())
        location = 60 + offset
        if name.startswith('#1/'):
            nameLen = int(name[3:])
            size = size - nameLen
            location = location + nameLen
            fileobj.seek(60+offset)
            name = fileobj.read(nameLen)
            (name,) = struct.unpack(str(nameLen)+'s', name)
            name = name.decode().strip()
    return (name, location, size)


def find_symtab(location, size):
    with open(staticLibPath, 'rb') as fileobj:
        fileobj.seek(location)
        magic = fileobj.read(4)
        (magic,) = struct.unpack('I', magic)
        # arm64 mach-o magic
        if not magic == 0xFEEDFACF:
            exit('静态库里的machO文件不是arm64平台的！')
        fileobj.seek(location+16)
        num_command = fileobj.read(4)
        (num_command,) = struct.unpack('I', num_command)
        offset = location+32
        while num_command > 0:
            fileobj.seek(offset)
            cmd = fileobj.read(4)
            (cmd,) = struct.unpack('I', cmd)
            if cmd == 0x2: # LC_SYMTAB = 0x2
                offset = offset + 16
                fileobj.seek(offset)
                stroff = fileobj.read(4)
                (stroff,) = struct.unpack('I', stroff)
                strsize = fileobj.read(4)
                (strsize,) = struct.unpack('I', strsize)
                symtabList_loc_size.append((stroff+location, strsize))
                break
            cmd_size = fileobj.read(4)
            (cmd_size,) = struct.unpack('I', cmd_size)
            offset = offset + cmd_size



def replace_Objc_MsgSend(fileLen):
    print('开始替换objc_msgSend...(静态库很大的话，可能需要等十几秒)!!!')
    pos = 0
    bytes = b''
    (loc, size) = symtabList_loc_size[0]
    listIndex = 1
    with open(staticLibPath, 'rb') as fileobj:
        while pos < fileLen:
            if pos == loc:
                content = fileobj.read(size)
                content = content.replace(b'\x00_objc_msgSend\x00', b'\x00_hook_msgSend\x00')
                pos = pos + size
                if listIndex < len(symtabList_loc_size):
                    (loc, size) = symtabList_loc_size[listIndex]
                    listIndex = 1 + listIndex
            else:
                step = 4
                if loc > pos:
                    step = loc - pos
                else:
                    step = fileLen - pos
                content = fileobj.read(step)
                pos = pos + step
            bytes = bytes + content
    with open(staticLibPath, 'wb+') as fileobj:
        print('开始写入文件...')
        fileobj.write(bytes)
        print('处理完了！！！')




need_process_objFile = set() # set('xx1', 'xx2') 表示静态库中，仅xx1跟xx2需要处理
needless_process_objFile = set() # set('xx1', 'xx2') 表示静态库中，xx1跟xx2不需要处理，剩下的都需要处理

def process_object_file(name, location, size):
    # 根据需要，下面三行中，只需打开一行，另外两行需要注释掉
    process_mode = 'default' # 默认处理该静态库中的所有目标文件(类)
    #process_mode = 'need_process_objFile' # 只处理need_process_objFile集合(上面的集合，需要赋值)中的类
    #process_mode = 'needless_process_objFile' # 除了needless_process_objFile集合(上面的集合，需要赋值)中的类不处理，剩下的都需要处理

    # 这里可以过滤不需要处理的目标文件，或者只选择需要处理的目标文件
    # 默认处理该静态库中的所有目标文件
    if process_mode == 'need_process_objFile':
        if name in need_process_objFile:
            find_symtab(location, size)
    elif process_mode == 'needless_process_objFile':
        if not name in need_process_objFile:
            find_symtab(location, size)
    else:
        find_symtab(location, size)
    



# 静态库的路径
staticLibPath = '完整的静态库路径'
# objc_msgSend被替换的名字（两者长度需一致）
# hookObjcMsgSend-arm64.s里定义了函数名为hook_msgSend，如果修改脚本里的函数名，hookObjcMsgSend-arm64.s里的函数名，也需跟脚本保持一致
# 建议不修改hook_msgSend
hook_msgSend_method_name = 'hook_msgSend'
symtabList_loc_size = list()


if __name__ == '__main__':
    # staticLibPath = '/Users/xx/xx/xx'.strip()
    staticLibPath = input('请输入静态库的路径：').strip()
    if not len(hook_msgSend_method_name) == len('objc_msgSend'):
        exit('need len(\'hook_msgSend\') == len(\'objc_msgSend\')!')
    isValid, desc = get_valid_staticLib_path()
    if not isValid:
        exit(desc)
    # 找到每个目标文件里的字符串表location 跟 size
    fileLen = Path(staticLibPath).stat().st_size
    offset = 8
    while offset < fileLen:
        (name, location, size) = resolver_object_header(offset)
        offset = location+size
        endIndex = name.find('.o')
        if endIndex == -1:
            #静态库的符号表，不需要处理
            continue
        process_object_file(name[:endIndex], location, size)
    if len(symtabList_loc_size) > 0:
        replace_Objc_MsgSend(fileLen)




