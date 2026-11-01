struct Inner_60099d14 { char pad0[0x3a8]; unsigned int value; };
struct Outer_60099d14 { char pad0[0x1428]; Inner_60099d14 *inner; };

extern "C" int func_60099d14(Outer_60099d14 *outer, unsigned int mask)
{
    return (outer->inner->value & mask) == mask;
}