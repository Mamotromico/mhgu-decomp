extern "C" void func_606a949c(char *p, int a1)
{
    *(int *)(p + 0x2c) = 0;
    *(int *)(p + 0x30) = 0;
    *(int *)(p + 0x34) = 0;
    *(char *)(p + 0x46) = 0;
    *(char *)(p + 0x47) = 0;
    *(char *)(p + 0x48) = 0;
    *(char *)(p + 0x44) = 1;

    int a = 0xc;
    int b = 0x40;
    if ((unsigned)a1 <= 2) {
        if (*(unsigned char *)(p + 0x45) == 0) {
            b = 0xa;
            a = 0x3;
            *(int *)(p + 0x40) = a1;
        }
    }
    *(int *)(p + 0x38) = a;
    *(int *)(p + 0x3c) = b;
}