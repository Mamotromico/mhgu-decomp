extern "C" void *func_60b35c00(void *arg0, void *arg1, unsigned int arg2)
{
    void *result = 0;
    void *node = arg1;
    goto check;
loop:
    node = *(void **)node;
check:
    if (node == 0)
        return result;
    if (*(unsigned char *)((char *)node + 0x28) != 0x18)
        goto loop;
    if (*(unsigned int *)((char *)node + 4) != arg2)
        goto loop;
    result = node;
    return result;
}