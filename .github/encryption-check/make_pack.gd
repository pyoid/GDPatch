extends SceneTree

func _initialize():
    var args = OS.get_cmdline_user_args()
    var directory_encrypted = args[1] == "encrypted"
    var files_encrypted = args[1] != "plain"
    ProjectSettings.set_setting("application/config/features", PackedStringArray(["4.5", "GL Compatibility"]))
    assert(ProjectSettings.save_custom("res://project.binary") == OK)
    var pack = PCKPacker.new()
    assert(pack.pck_start(args[0], 32, "0".repeat(64), directory_encrypted) == OK)
    for path in ["project.binary", "main.gd", "untouched.gd", "untouched.txt"]:
        assert(pack.add_file("res://" + path, "res://" + path, files_encrypted) == OK)
    for i in range(200):
        assert(pack.add_file("res://padding/file_%03d.txt" % i, "res://untouched.txt", files_encrypted) == OK)
    assert(pack.flush() == OK)
    quit()
