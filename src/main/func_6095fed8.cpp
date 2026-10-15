extern "C" void func_6095fed8(void *p, float value)
{
    struct Layout {
        unsigned char pad[0x70];
        float field;
    };
    ((Layout *)p)->field = value;
}