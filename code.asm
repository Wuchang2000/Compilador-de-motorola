DDRA   EQU   $1001

    ORG $8000

    NOP

    ADCA #$F0
    ADCA #$DDAA

    LDAA $45,X
    STAA  DDRA

    LDY $AB
    LDAA $45,X

CICLO
    LDY $AB

    BEQ CICLO

    LDAA  $457C   *Buenas

*Buenas 

    END