extern "C" void func_6131e79c(unsigned char *obj, unsigned char *src) {
    if (*(unsigned long long *)(obj + 0x38) != 0) {
        if (obj[0x2e] == 0) {
            return;
        }
    }
    *(unsigned short *)(obj + 0x14) = *(unsigned short *)(src + 0xc);
}