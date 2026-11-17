extern "C" void func_609fd584(int *unused, char *p, int n)
{
    *(int *)(p + 0x8) = ((*(int *)(p + 0x4)) ? *(int *)(p + 0x4) + (n << 6) : 0);
    *(int *)(p + 0x20) = ((*(int *)(p + 0x1c)) ? *(int *)(p + 0x1c) + (n << 6) : 0);
}