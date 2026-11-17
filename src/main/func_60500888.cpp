extern "C" char *func_604f9040(void *);

extern "C" unsigned char func_60500888(char *p) {
    return *(unsigned char *)(func_604f9040(*(void **)(p + 0x3bc)) + 0xf);
}