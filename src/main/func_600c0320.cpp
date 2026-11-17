extern "C" void func_600c0320(char *base)
{
    if (*(unsigned char *)(base + 0x73e4) == 0) {
        if (*(unsigned char *)(base + 0x73e5) != 0)
            return;
        char *p = *(char **)(base + 0x1428);
        *(unsigned char *)(p + 0x5ad) = 0;
    }
}