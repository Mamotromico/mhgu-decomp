extern "C" void func_6022c624(char *p, unsigned char v)
{
    *(unsigned char *)(p + 0x63e) = v;
    *(unsigned char *)(p + 0x16258) = v;
    if (v == 1) {
        *(unsigned char *)(p + 0x63f) = 0;
        *(unsigned char *)(p + 0x640) = 0;
    }
}