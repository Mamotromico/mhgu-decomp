extern "C" int func_60627aac(char *base, int index) {
    int *table = (int *)(base + (index << 2));
    int *p = (int *)table[0x6c / 4];
    if (p) {
        unsigned char flag = *((unsigned char *)p + 0xa0);
        int r = 1;
        if (flag != 0)
            return r;
    }
    return 0;
}