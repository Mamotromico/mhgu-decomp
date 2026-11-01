extern "C" void func_60600e88(char *p, unsigned int v)
{
    unsigned int a;
    unsigned int b;

    *(unsigned int *)(p + 0x68) = v;
    if (v == 0) {
        a = 4;
        b = 8;
    } else {
        a = 1;
        b = 2;
    }
    *(unsigned int *)(p + 0x70) = a;
    *(unsigned int *)(p + 0x74) = b;
}