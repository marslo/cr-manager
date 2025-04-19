#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import List

try:
    from libs.helper import ColorHelpFormatter, COLOR_BOLD, COLOR_RESET, COLOR_DEBUG, COLOR_CYAN, COLOR_YELLOW
    from libs.manager import CopyrightManager, detect_file_format
except ImportError as e:
    print(f"Error: Failed to import from 'libs' package. Make sure it's accessible and contains helper.py and manager.py.")
    print(f"Details: {e}")
    sys.exit(1)

# Configuration specific to the main script execution
DEFAULT_COPYRIGHT_FILE = "COPYRIGHT.txt"

# ====================== 命令行处理 ======================
def main():
    parser = argparse.ArgumentParser(
        prog='cr_manager',
        description=COLOR_BOLD + '自动添加/更新/删除多格式版权声明' + COLOR_RESET,
        formatter_class=ColorHelpFormatter,
        add_help=False # Manually add help for better control
    )

    # ====================== 参数分组 ======================
    pos_group = parser.add_argument_group(
        COLOR_BOLD + 'POSITIONAL ARGUMENTS' + COLOR_RESET
    )
    action_group = parser.add_argument_group(
        COLOR_BOLD + 'ACTION MODES (choose one, default is add)' + COLOR_RESET
    )
    option_group = parser.add_argument_group(
        COLOR_BOLD + 'OPTIONS' + COLOR_RESET
    )

    # ====================== 位置参数 ======================
    pos_group.add_argument(
        'files',
        nargs='*', # Allows zero or more files
        metavar='FILES',
        help='要处理的目标文件或目录列表'
    )

    # ====================== 操作模式（互斥组） ======================
    action = action_group.add_mutually_exclusive_group()
    action.add_argument('--check',action='store_true',help='检查模式: 检查文件版权状态 (存在且匹配/存在需更新/不存在)')
    action.add_argument('--delete',action='store_true',help='删除模式: 删除检测到的版权声明')
    action.add_argument('--update',action='store_true',help='更新模式: 强制替换或添加版权声明 (如果不存在)')

    # ====================== 选项参数 ======================
    option_group.add_argument('--copyright-file',metavar='FILE',type=Path,default=Path(DEFAULT_COPYRIGHT_FILE),help=f'指定版权模板文件路径 (默认: {DEFAULT_COPYRIGHT_FILE})')
    option_group.add_argument('--filetype',metavar='TYPE',help="强制文件类型格式, 覆盖自动检测 (例如 'python', 'java').\n如果只提供此参数(无文件路径), 则显示该类型的格式化预览。")
    option_group.add_argument('--recursive', '-r',action='store_true',help='如果 FILES 包含目录，则递归处理其中的文件')
    option_group.add_argument('--debug',action='store_true',help='调试模式: 显示将应用于文件的格式化版权内容, 但不修改文件。')
    option_group.add_argument('-v', '--verbose',action='store_true',help='显示详细的处理摘要信息')
    option_group.add_argument('-h', '--help',action='help',default=argparse.SUPPRESS,help='显示此帮助信息并退出')
    option_group.add_argument('--version',action='version',version='%(prog)s 1.2', help="显示程序版本号并退出")

    args = parser.parse_args()

    # --- Handle Implicit Debug Format Mode ---
    is_action_mode = args.check or args.delete or args.update or args.debug
    if args.filetype and not args.files and not is_action_mode:
        if args.verbose:
            print(f"信息: 进入格式预览模式 (因为只提供了 --filetype)...")
        try:
            manager = CopyrightManager(args.copyright_file)
        except SystemExit as e:
             print(f"错误: 无法加载版权文件 '{args.copyright_file}' 进行预览。", file=sys.stderr)
             sys.exit(e.code)

        fmt_key = manager.filetype_map.get(args.filetype.lower())
        if not fmt_key:
            dummy_path = Path(f"preview.{args.filetype.lower()}")
            # Use the imported function directly
            fmt_key = detect_file_format(dummy_path, args.filetype.lower())
            if not fmt_key:
                print(f"错误: 无效或不支持的文件类型 '{args.filetype}' 用于预览格式。", file=sys.stderr)
                # Display supported types here as well
                print(f"提示: 支持的文件类型包括: {', '.join(manager.supported_types)}")
                print(f"提示: 也可尝试使用已知的后缀名 (例如 'py', 'java') 作为类型。", file=sys.stderr)
                sys.exit(1)
            else:
                 if args.verbose:
                     print(f"信息: 文件类型 '{args.filetype}' 通过启发式检测映射到格式 '{fmt_key}'", file=sys.stderr)

        formatted = manager._format_copyright(fmt_key)
        if formatted:
            if args.verbose: print(f"--- 版权格式预览 ({args.filetype} / 格式键: {fmt_key}) ---")
            print(f"{COLOR_DEBUG}{formatted}{COLOR_RESET}") # Always print formatted block
            if args.verbose: print("--- 预览结束 ---")
            sys.exit(0)
        else:
            print(f"错误: 无法为格式 '{fmt_key}' 生成格式化预览。", file=sys.stderr)
            sys.exit(1)
    # --- End of Implicit Debug Format Mode Handling ---

    # --- Validate arguments for standard operation modes ---
    if not args.files:
        parser.error("至少需要指定一个目标文件或目录进行操作。使用 --filetype <type> (无文件) 进行格式预览，或使用 -h 获取帮助。")

    # --- Initialize CopyrightManager for standard operations ---
    try:
        manager = CopyrightManager(args.copyright_file)
    except SystemExit as e:
        sys.exit(e.code)

    # --- Process Files ---
    files_to_process: List[Path] = []
    for item_str in args.files:
        item_path = Path(item_str)
        if item_path.is_dir():
            if args.recursive:
                if args.verbose:
                    print(f"信息: 正在递归扫描目录 {item_path} ...")
                files_to_process.extend(p for p in item_path.rglob('*') if p.is_file())
            else:
                print(f"警告: '{item_path}' 是一个目录，但未指定 --recursive。已跳过。", file=sys.stderr)
        elif item_path.is_file():
            files_to_process.append(item_path)
        else:
            print(f"警告: '{item_path}' 不存在或不是有效的文件/目录。已跳过。", file=sys.stderr)

    if not files_to_process:
        print("错误: 未找到有效文件进行处理。", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"信息: 将处理 {len(files_to_process)} 个文件...")

    exit_code = 0
    processed_count = 0
    skipped_count = 0
    updated_count = 0
    added_count = 0
    deleted_count = 0
    error_count = 0
    debug_shown_count = 0
    forced_type = args.filetype.lower() if args.filetype else None
    # Get supported types string once before the loop
    supported_types_str = ', '.join(manager.supported_types)

    for path in files_to_process:
        processed_count += 1
        # Per-file status is printed regardless of verbosity for now
        print(f"[{processed_count}/{len(files_to_process)}] 处理: {path} ... ", end="")

        # --- Debug Mode Check ---
        if args.debug:
            formatted = manager.format_for_file(path, forced_type)
            if formatted:
                print(f"调试输出 (格式化内容):")
                print(f"{COLOR_DEBUG}{formatted}{COLOR_RESET}")
                debug_shown_count += 1
            else:
                # format_for_file might print info, add context here
                print(f"{COLOR_YELLOW}调试: 无法为此文件生成格式化版权 (文件类型可能不支持或读取错误){COLOR_RESET}")
                error_count += 1; exit_code = 1 # Treat inability to format in debug as error
            continue # Go to next file in debug mode

        # --- Standard Action Modes ---
        success = False
        msg = "未知操作"
        try:
            if args.check:
                success, msg = manager.check_copyright_status(path, forced_type)
                if msg == "match": print(f"状态: 已存在且匹配"); skipped_count += 1
                elif msg == "mismatch": print(f"状态: {COLOR_YELLOW}需要更新{COLOR_RESET}"); exit_code = 1
                elif msg == "not_found": print(f"状态: {COLOR_YELLOW}未找到{COLOR_RESET}"); exit_code = 1
                elif msg == "unsupported_format":
                    print(f"状态: 不支持的文件格式")
                    print(f"提示: 支持的文件类型包括: {supported_types_str}")
                    error_count += 1 # Count unsupported as error for summary
                elif msg.startswith("error:"):
                    print(f"状态: {COLOR_BOLD}检查错误: {msg}{COLOR_RESET}")
                    error_count += 1; exit_code = 1
                else: # Unexpected message
                     print(f"状态: 未知检查结果 '{msg}'")
                     error_count += 1; exit_code = 1

            elif args.delete:
                success, msg = manager.delete_copyright(path, forced_type)
                if success: print(f"操作: {COLOR_YELLOW}已删除{COLOR_RESET}"); deleted_count += 1
                elif msg == "not_found": print(f"操作: 未找到可删除的版权"); skipped_count +=1
                elif msg == "unsupported_format":
                    print(f"操作: 不支持的文件格式，无法删除")
                    print(f"提示: 支持的文件类型包括: {supported_types_str}")
                    error_count += 1
                elif msg.startswith("error:"):
                    print(f"操作: {COLOR_BOLD}删除错误: {msg}{COLOR_RESET}")
                    error_count += 1; exit_code = 1
                else: # Unexpected message
                     print(f"操作: 未知删除结果 '{msg}'")
                     error_count += 1; exit_code = 1

            elif args.update:
                success, msg = manager.update_copyright(path, forced_type)
                if success:
                    if msg == "updated": print(f"操作: {COLOR_CYAN}已更新{COLOR_RESET}"); updated_count += 1
                    elif msg == "inserted": print(f"操作: {COLOR_CYAN}已添加 (因未找到旧版){COLOR_RESET}"); added_count += 1
                    else: print(f"操作: 完成 ({msg})") # Should ideally be updated/inserted
                elif msg == "unsupported_format":
                    print(f"操作: 不支持的文件格式，无法更新")
                    print(f"提示: 支持的文件类型包括: {supported_types_str}")
                    error_count += 1
                elif msg == "generate_failed":
                     print(f"操作: {COLOR_BOLD}更新错误: 无法生成目标格式版权{COLOR_RESET}")
                     error_count += 1; exit_code = 1
                elif msg.startswith("error:"):
                    print(f"操作: {COLOR_BOLD}更新错误: {msg}{COLOR_RESET}")
                    error_count += 1; exit_code = 1
                else: # Unexpected message
                     print(f"操作: 未知更新结果 '{msg}'")
                     error_count += 1; exit_code = 1

            else: # Default action: Add
                success, msg = manager.add_copyright(path, forced_type)
                if success:
                    if msg == "skipped": print(f"操作: 已跳过 (已存在且匹配)"); skipped_count += 1
                    elif msg == "updated": print(f"操作: {COLOR_CYAN}已更新 (因不匹配){COLOR_RESET}"); updated_count +=1
                    elif msg == "inserted" or msg == "added": print(f"操作: {COLOR_CYAN}已添加{COLOR_RESET}"); added_count +=1
                    else: print(f"操作: 完成 ({msg})") # Should ideally be one of the above
                elif msg == "unsupported_format":
                    print(f"操作: 不支持的文件格式，无法添加")
                    print(f"提示: 支持的文件类型包括: {supported_types_str}")
                    error_count += 1
                elif msg == "generate_failed":
                     print(f"操作: {COLOR_BOLD}添加错误: 无法生成目标格式版权{COLOR_RESET}")
                     error_count += 1; exit_code = 1
                elif msg.startswith("error:"):
                    print(f"操作: {COLOR_BOLD}添加错误: {msg}{COLOR_RESET}")
                    error_count += 1; exit_code = 1
                else: # Unexpected message
                     print(f"操作: 未知添加结果 '{msg}'")
                     error_count += 1; exit_code = 1

        except Exception as e:
            # Catch unexpected errors during processing a single file
            print(f"{COLOR_BOLD}意外错误处理文件 {path}: {e}{COLOR_RESET}")
            error_count += 1
            exit_code = 1 # Indicate failure

    # --- Final Summary ---
    if args.verbose:
        print("\n--- 处理结果 ---")
        print(f"总文件数: {len(files_to_process)}")
        if args.debug: print(f"调试预览已显示: {debug_shown_count}")
        elif args.check: print(f"匹配: {skipped_count}"); print(f"需要操作/未找到: (见上面日志)")
        else: print(f"已添加: {added_count}"); print(f"已更新: {updated_count}"); print(f"已删除: {deleted_count}"); print(f"已跳过: {skipped_count}")
        # Renamed last category for clarity
        print(f"错误/不支持/无法格式化(调试): {error_count}")
        print("---------------")
        if exit_code != 0:
            if args.debug: print("调试完成，部分文件无法格式化。")
            elif args.check: print("检查完成，部分文件需要操作或遇到错误/不支持。")
            else: print("处理完成，但遇到一个或多个错误/不支持。")
        # Print success only if not debugging and no errors occurred
        elif not args.debug and exit_code == 0:
            print("处理成功完成。")

    sys.exit(exit_code)

if __name__ == "__main__":
    main()

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
