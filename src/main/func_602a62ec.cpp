extern "C" int func_602a3e50(int, float, int);

extern "C" int func_602a62ec(int a, int b)
{
    if (b >= 0x96)
        b = 0x96;
    b = (b + b * 2) * 2;
    float f = -(float)b;
    return func_602a3e50(a, f, 1);
}