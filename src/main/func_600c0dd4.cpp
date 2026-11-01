extern "C" int func_600c0dd4(void *p)
{
    char *base = *(char **)((char *)p + 0x1428);
    float v = *(float *)(base + 0x5db8);
    return v > 0.0f ? 1 : 0;
}