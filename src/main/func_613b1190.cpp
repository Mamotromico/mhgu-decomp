extern "C" void func_613b1190(char *base)
{
    int count = *(int *)(base + 0x300);
    if (count >= 1) {
        char *p = base + 0x4;
        int i = 0;
        do {
            *(int *)(p + 0x0) = 0;
            i = i + 1;
            *(int *)(p + 0x4) = 0;
            p += 0x18;
            count = *(int *)(base + 0x300);
        } while (i < count);
    }
    *(int *)(base + 0x304) = 0;
    *(int *)(base + 0x328) = 0;
    *(int *)(base + 0x32c) = 0;
}