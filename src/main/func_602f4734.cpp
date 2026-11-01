extern "C" void func_602f4734(char *obj, float delta)
{
    float *field = (float *)(obj + 0x2990);
    float nv = *field - delta;
    *field = nv;
    if (nv <= 0.0f)
        *(unsigned short *)(obj + 0x2984) = 0;
}