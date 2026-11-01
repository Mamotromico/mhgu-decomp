extern "C" void func_6009dbcc(char *r0, unsigned r1, unsigned r2, int r3)
{
    if (r1 > 7)
        return;
    if (r3 == 0)
        return;
    unsigned short *p = (unsigned short *)(*(char **)(r0 + 0x1428) + 0x4d8);
    *p = *p + (unsigned short)r3;
    (void)r2;
}