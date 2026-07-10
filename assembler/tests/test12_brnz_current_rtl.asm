; Current RTL behavior: BRNZ branches when N OR Z is set.
        LI    R1, 0
        BRNZ  TAKEN
        LI    R2, 999
TAKEN:
        LI    R3, 5
        STOP
