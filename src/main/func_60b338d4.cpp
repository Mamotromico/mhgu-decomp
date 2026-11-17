extern "C" void func_60b338d4(char *r0, char *r1)
{
    *(char **)(r0 + 0x4) = r1;
    unsigned base = (unsigned)r1 + 0x188;
    unsigned r12 = 0;
    do {
        char *r3 = r0 + r12;
        unsigned r2 = base - 0x184;
        r12 += 0x70;
        *(unsigned *)(r3 + 0xc) = r2;
        *(unsigned *)(r3 + 0x68) = base;
        *(unsigned *)(r3 + 0x14) = r2;
        *(unsigned *)(r3 + 0x1c) = r2;
        *(unsigned *)(r3 + 0x24) = r2 = base - 0x174;
        *(unsigned *)(r3 + 0x2c) = r2 = base - 0x16c;
        *(unsigned *)(r3 + 0x34) = r2 = base - 0x164;
        *(unsigned *)(r3 + 0x3c) = r2 = base - 0x15c;
        *(unsigned *)(r3 + 0x44) = r2 = base - 0x154;
        *(unsigned *)(r3 + 0x4c) = r2 = base - 0x14c;
        *(unsigned *)(r3 + 0x54) = r2 = base - 0x144;
        *(unsigned *)(r3 + 0x5c) = r2 = base - 0x13c;
        *(unsigned *)(r3 + 0x64) = r2 = base - 0x134;
        base += 0x21c;
    } while (r12 != 0x7e0);
}