extern "C" void func_605bc584(void *arg0, unsigned int arg1)
{
    struct Inner {
        char pad0[0x4c];
        unsigned int value;
    };

    struct Outer {
        char pad0[0xac];
        Inner *inner;
    };

    Outer *outer = (Outer *)arg0;
    Inner *inner = outer->inner;

    if (inner)
        inner->value = arg1;
}