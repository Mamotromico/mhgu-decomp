extern "C" int *func_600c0368(char *p)
{
    int value = 2;
    int *result = *(int **)(p + 0x1428);
    *(int *)((char *)result + 0x5de8) = value;
    return result;
}