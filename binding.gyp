{
  "targets": [
    {
      "target_name": "upgp_seccomp_native",
      "sources": [ "src/native/upgp_seccomp_native.c" ],
      "include_dirs": [
        "<!(node -e \"require('node-addon-api').include\")"
      ],
      "cflags!": [ "-fno-exceptions" ],
      "cflags_cc!": [ "-fno-exceptions" ]
    }
  ]
}
