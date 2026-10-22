extern "C" void func_60595b2c(void *obj, unsigned int val1, unsigned int val2)
{
    if (val1 == 0)
        return;

    if (val2 != 0) {
        *(unsigned int *)((char *)obj + 0x4c) = val1;
        *(unsigned int *)((char *)obj + 0x50) = val2;
    }
}