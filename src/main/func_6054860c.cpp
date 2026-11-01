extern "C" void func_6054860c(char *p, int x)
{
    if (x != 1) {
        *(int *)(p + 0x29c) = -1;
        return;
    }
    *(int *)(p + 0x29c) = 0;
    *(int *)(p + 0x2a0) = 1;
}