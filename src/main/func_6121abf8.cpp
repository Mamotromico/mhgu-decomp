extern "C" void func_6121abf8(char *p, unsigned char v)
{
    p[0x10] = (char)v;
    p[0x8] = 0;
    *(int *)(p + 0x14) = 0;
    *(int *)(p + 0x18) = 0;
    *(int *)(p + 0x1c) = 0;
    p[0x25] = 0;
    p[0x26] = (char)0xff;
}