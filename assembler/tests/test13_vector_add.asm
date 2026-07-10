        LI    R1, $0100

        VLD   V1, R1, 0
        VLD   V2, R1, 8

        VADD  V3, V1, V2

        STOP

        .ORG  $0100

        ; V1 bytes: 01 02 03 04 05 06 07 08
        .DW   $0201
        .DW   $0403
        .DW   $0605
        .DW   $0807

        ; V2 bytes: 01 01 01 01 01 01 01 01
        .DW   $0101
        .DW   $0101
        .DW   $0101
        .DW   $0101