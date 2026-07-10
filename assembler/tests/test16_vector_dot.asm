        LI    R1, $0100

        VLD   V1, R1, 0
        VLD   V2, R1, 8

        VACLR
        VDOT  V1, V2

        STOP

        .ORG  $0100

        ; V1: eight signed bytes equal to 1
        .DW   $0101
        .DW   $0101
        .DW   $0101
        .DW   $0101

        ; V2: eight signed bytes equal to 2
        .DW   $0202
        .DW   $0202
        .DW   $0202
        .DW   $0202