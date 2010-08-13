#ifndef LL_LL_H
#define LL_LL_H

#include <stdbool.h>

struct ll_lens_t
{
    double x, y, mass;
};

struct ll_lenses_t
{
    unsigned num_lenses;
    struct ll_lens_t *lens;
};

struct ll_rect_t
{
    double x, y, width, height;
};

struct ll_magpattern_param_t
{
    struct ll_lenses_t lenses;
    struct ll_rect_t region;
    unsigned xpixels, ypixels;
    double pixels_per_width, pixels_per_height;
};

extern void
ll_init_magpattern_params(struct ll_magpattern_param_t *params,
                          const struct ll_lenses_t *lenses,
                          const struct ll_rect_t *region,
                          unsigned xpixels, unsigned ypixels);

enum ll_rayshooting_kernel_t
{
    LL_KERNEL_SIMPLE,
    LL_KERNEL_BILINEAR,
    LL_KERNEL_TRIANGULATED
};

struct ll_rayshooter_t
{
    struct ll_magpattern_param_t *params;
    enum ll_rayshooting_kernel_t kernel;
    unsigned levels;
    int refine;
    int refine_final;
    bool cancel;
};

extern void
ll_init_rayshooter(struct ll_rayshooter_t *rs,
                   struct ll_magpattern_param_t *params, unsigned levels);

extern void
ll_cancel_rayshooter(struct ll_rayshooter_t *rs);

extern bool
ll_shoot_single_ray(const struct ll_magpattern_param_t *params,
                    double x, double y, double *mag_x, double *mag_y);

extern void
ll_rayshoot_rect(const struct ll_magpattern_param_t *params, int *magpat,
                 const struct ll_rect_t *rect, int xrays, int yrays);

struct ll_patches_t
{
    struct ll_rect_t rect;
    int xrays, yrays;
    double width_per_xrays, height_per_yrays;
    char* hit;
    unsigned num_patches;
};

extern void
ll_get_subpatches(const struct ll_magpattern_param_t *params,
                  struct ll_patches_t *patches);

extern void
ll_rayshoot_subpatches(const struct ll_rayshooter_t *rs, void *magpat,
                       const struct ll_patches_t *patches,
                       unsigned level, double *progress);

extern void
ll_finalise_subpatches(const struct ll_rayshooter_t *rs, void *magpat,
                       const struct ll_patches_t *patches);

extern void
ll_rayshoot(const struct ll_rayshooter_t *rs, void *magpat,
            const struct ll_rect_t *rect, int xrays, int yrays,
            double *progress);

extern void
ll_ray_hit_pattern(const struct ll_magpattern_param_t *params, char *buf,
                   const struct ll_rect_t *rect);

extern void
ll_source_images(const struct ll_magpattern_param_t *params, char *buf,
                 const struct ll_rect_t *rect, int xrays, int yrays,
                 int refine, double source_x, double source_y, double source_r);

extern void
ll_render_magpattern_greyscale(const float *magpat, char *buf, unsigned size);

extern void
ll_light_curve(const struct ll_magpattern_param_t *params, const float *magpat,
               double *curve, unsigned num_points,
               double x0, double y0, double x1, double y1);

#endif
