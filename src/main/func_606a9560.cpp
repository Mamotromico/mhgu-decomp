extern "C" void func_606a9560(char *p, int v)
{
    unsigned char flag = *(unsigned char *)(p + 0x44);
    if (flag != 0)
        return;
    *(unsigned char *)(p + 0x44) = 1;
    *(int *)(p + 0x38) = 0x11;
    *(int *)(p + 0x3c) = 0x5e;
    *(int *)(p + 0x40) = v;
}