        LI    R1, $0100

        VLD   V1, R1, 0

        VRELU V2, V1

        STOP

        .ORG  $0100

        ; V1 = 7F80FF01AA5500FE
        ; Lowest byte is FE because lane 0 is stored at the lowest address.
        .DW   $00FE
        .DW   $AA55
        .DW   $FF01
        .DW   $7F80