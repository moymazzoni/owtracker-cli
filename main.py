import sys

if __name__ == '__main__':
    try:
        import init_startup
        from cli.menu import menu_loop
        config = init_startup.init()
        menu_loop(config)
    except KeyboardInterrupt:
        sys.exit(130)
    except EOFError:
        sys.exit(1)