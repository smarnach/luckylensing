// Lucky Lensing Library (http://github.com/smarnach/luckylensing)
// Copyright 2010 Sven Marnach

#ifndef LL_LL_H
#define LL_LL_H

#include <stdbool.h>

struct ll_lens
{
    double x, y, mass;
};

struct ll_lenses
{
    unsigned num_lenses;
    struct ll_lens *lens;
};

struct ll_rect
{
    double x, y, width, height;
};

struct ll_magpat_params
{
    struct ll_lenses lenses;
    struct ll_rect region;
    unsigned xpixels, ypixels;
    double pixels_per_width, pixels_per_height;
};

extern void
ll_init_magpat_params(struct ll_magpat_params *params,
                      const struct ll_lenses *lenses,
                      const struct ll_rect *region,
                      unsigned xpixels, unsigned ypixels);

enum ll_rayshooting_kernel
{
    LL_KERNEL_SIMPLE,
    LL_KERNEL_BILINEAR,
    LL_KERNEL_TRIANGULATED
};

struct ll_rayshooter
{
    struct ll_magpat_params *params;
    enum ll_rayshooting_kernel kernel;
    int refine;
    int refine_final;
    bool cancel;
};

extern void
ll_init_rayshooter(struct ll_rayshooter *rs, struct ll_magpat_params *params);

extern void
ll_cancel_rayshooter(struct ll_rayshooter *rs);

extern int
ll_shoot_single_ray(const struct ll_magpat_params *params,
                    double x, double y, double *mag_x, double *mag_y);

extern void
ll_rayshoot_rect(const struct ll_magpat_params *params, int *magpat,
                 const struct ll_rect *rect, int xrays, int yrays);

struct ll_patches
{
    struct ll_rect rect;
    int xrays, yrays;
    unsigned level;
    double width_per_xrays, height_per_yrays;
    unsigned char* hit;
    unsigned num_patches;
};

extern void
ll_get_subpatches(const struct ll_magpat_params *params,
                  struct ll_patches *patches);

extern void
ll_rayshoot_subpatches(const struct ll_rayshooter *rs, void *magpat,
                       const struct ll_patches *patches, double *progress);

extern void
ll_finalise_subpatches(const struct ll_rayshooter *rs, void *magpat,
                       const struct ll_patches *patches);

extern void
ll_rayshoot(const struct ll_rayshooter *rs, void *magpat,
            const struct ll_rect *rect, int xrays, int yrays,
            unsigned levels, double *progress);

extern void
ll_ray_hit_pattern(const struct ll_magpat_params *params, unsigned
                   char *buf, const struct ll_rect *rect);

extern void
ll_source_images(const struct ll_magpat_params *params, unsigned char *buf,
                 const struct ll_rect *rect, int xrays, int yrays,
                 int refine, double source_x, double source_y, double source_r);

extern void
ll_render_magpat_greyscale(const float *magpat, unsigned char *buf,
                           unsigned xpixels, unsigned ypixels,
                           float min, float max);

extern void
ll_render_magpat_gradient(const float *magpat, unsigned char *buf,
                          unsigned xpixels, unsigned ypixels,
                          float min, float max,
                          const unsigned char colors[][3],
                          const unsigned *steps);

extern void
ll_light_curve(const struct ll_magpat_params *params, const float *magpat,
               float *curve, unsigned samples,
               double x0, double y0, double x1, double y1);

#endif
