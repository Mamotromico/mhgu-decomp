extern "C" void func_605d2130(char *base, unsigned int index, unsigned char value, unsigned short value2) {
    char *p = base + index * 12;
    *(unsigned char *)(p + 0x54) = value;
    *(unsigned short *)(p + 0x4e) = value2;
}