extern "C" int func_6005d410(char *p, unsigned idx, char *q)
{
    int result = 0;
    if (idx <= 9) {
        *(unsigned *)(p + idx * 4 + 0x1c) = (unsigned)q;
        *(unsigned *)(p + 0x44) += 1;
        char *r = *(char **)(q + 0x1428);
        *(unsigned char *)(r + 0x1b5) = (unsigned char)idx;
        result = 1;
    }
    return result;
}