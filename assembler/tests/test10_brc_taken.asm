LI    R1, $FFFF
        LI    R2, 1
        ADD   R3, R1, R2
        BRC   TAKEN
        LI    R4, 999
TAKEN:
        LI    R5, 5
        STOP
