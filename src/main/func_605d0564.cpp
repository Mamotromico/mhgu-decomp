struct Inner_605d0564 {
    char pad0[0x94];
    int (*func)(void *, int, int);
};

struct Middle_605d0564 {
    Inner_605d0564 *inner;
};

struct Outer_605d0564 {
    char pad0[0xb0];
    Middle_605d0564 *middle;
};

extern "C" int func_605d0564(Outer_605d0564 *outer, int arg)
{
    Middle_605d0564 *middle = outer->middle;
    return middle->inner->func(middle, arg, 0);
}