extern "C" void func_6054ee64(char *p, int v) {
    unsigned char d = *(unsigned char *)(p + 0x0e);
    *(unsigned short *)(p + 0x14) = (unsigned short)v;
    int q = (v + (int)d - 1) / (int)d;
    *(unsigned short *)(p + 0x12) = (unsigned short)q;
    *(unsigned short *)(p + 0x10) = 0;
    *(int *)(p + 0x1c) = 3;
    *(unsigned char *)(p + 0x20) = 1;
}