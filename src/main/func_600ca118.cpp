extern "C" int func_600ca118(void *p)
{
    void *q = *(void **)p;
    return ((int (*)(void *))*(void **)((char *)q + 0x3dc))(p);
}