extern "C" void *func_600710b0(void *p)
{
    void *q = *(void **)((char *)p + 0x75cc);
    if (!q)
        return 0;
    void *(*f)(void *) = *(void *(**)(void *))((char *)*(void **)q + 0x40);
    return f(q);
}