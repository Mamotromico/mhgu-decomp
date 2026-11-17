extern "C" int func_604f9040(void *);

extern "C" int func_6050086c(char *p)
{
    char *r = (char *)func_604f9040(*(void **)(p + 0x3bc));
    return *(unsigned char *)(r + 0xf) != 0 ? 1 : 0;
}