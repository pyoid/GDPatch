extends SceneTree

func _initialize():
    var marker = "original"
    if marker != "patched":
        push_error("script patch did not run")
        quit(1)
        return
    if FileAccess.get_file_as_string("res://untouched.txt") != "x".repeat(32768):
        push_error("unchanged file differs")
        quit(1)
        return
    if load("res://untouched.gd").new().value() != 37:
        push_error("unchanged script differs")
        quit(1)
        return
    var args = OS.get_cmdline_user_args()
    var pack = FileAccess.open(args[0], FileAccess.READ)
    pack.seek(20)
    if bool(pack.get_32() & 1) != (args[1] == "encrypted"):
        push_error("directory encryption flag differs")
        quit(1)
        return
    var position = pack.get_position()
    if pack.get_length() <= 10000 or pack.get_position() != position:
        push_error("pack length query failed")
        quit(1)
        return
    print("PACK_CHECK_OK: " + args[1])
    quit()
