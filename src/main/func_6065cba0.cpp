extern "C" void func_6056de60(void *p);

extern "C" void *func_6065cba0(char *obj, int index)
{
    void **table = *(void ***)(obj + 0x34);
    void *result = table[index];
    if (result)
        func_6056de60(result);
    return result;
}