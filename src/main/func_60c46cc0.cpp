extern "C" void func_60c46cc0(char *r0, unsigned r1, unsigned r2, char r3) {
    if (r1 == 0xffffffffu) return;
    if (*(unsigned *)(r0 + 0xbc) <= r1) return;
    char *p = *(char **)(r0 + 0xc8);
    char *q = *(char **)(p + r1 * 4);
    if (!q) return;
    if (*(unsigned *)(q + 0x5c) <= r2) return;
    char *addr = *(char **)(q + 0x58) + (r2 << 6);
    if (!addr) return;
    *(char *)(addr + 0xc) = r3;
}