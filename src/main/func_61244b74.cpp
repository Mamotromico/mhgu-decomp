extern "C" int func_6122a5fc(void *p);

extern "C" int func_61244b74(void *p)
{
    int v = *(int *)((char *)p + 8);
    int r = func_6122a5fc(p);
    return v == r ? 1 : 0;
}