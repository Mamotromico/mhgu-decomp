extern "C" int func_602481cc(char *p);

extern "C" int func_6023d790(int);

extern "C" int func_602481cc(char *p)
{
    int v = *(int *)(p + 0xc);
    if (v == 0)
        return 0;
    return func_6023d790(v);
}