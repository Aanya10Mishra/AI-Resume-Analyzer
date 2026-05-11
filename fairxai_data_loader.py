"""
Fair-XAI Data Loader & Integration
Loads Kaggle (CSV) and Synthetic (XLSX) datasets for fairness analysis

Datasets:
1. preprocessed_resumes(1).csv - Real Kaggle data
2. Resume_Dataset_600_Balanced(1).xlsx - Synthetic 600-resume balanced dataset
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, Tuple, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FairXAIDataLoader:
    """
    Load and preprocess both Kaggle (real) and Synthetic datasets
    Standardize formats for Fair-XAI framework
    """
    
    def __init__(self, downloads_dir: str = None, project_dir: str = None):
        """
        Initialize data loader
        
        Args:
            downloads_dir: Path to Downloads folder (where original files are)
            project_dir: Path to AI Resume Analyzer project directory
        """
        if downloads_dir is None:
            downloads_dir = str(Path.home() / "Downloads")
        if project_dir is None:
            project_dir = str(Path.home() / "Documents" / "AI Resume Analyzer")
        
        self.downloads_dir = downloads_dir
        self.project_dir = project_dir
        
        logger.info(f"✅ Data loader initialized")
        logger.info(f"   Downloads: {downloads_dir}")
        logger.info(f"   Project: {project_dir}")
    
    # ============================================================================
    # KAGGLE DATASET (REAL DATA)
    # ============================================================================
    
    def load_kaggle_data(self, filename: str = "preprocessed_resumes (1).csv") -> pd.DataFrame:
        """
        Load real Kaggle resume dataset
        
        Args:
            filename: CSV filename in Downloads folder
        
        Returns:
            Processed DataFrame with standardized columns
        """
        
        filepath = Path(self.downloads_dir) / filename
        
        logger.info(f"\n{'='*80}")
        logger.info(f"LOADING KAGGLE DATASET (REAL DATA)")
        logger.info(f"{'='*80}")
        logger.info(f"📂 Loading from: {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            logger.info(f"✅ Loaded: {len(df)} records, {len(df.columns)} columns")
            
            # Display available columns
            logger.info(f"\n📊 Columns found:")
            for col in df.columns:
                logger.info(f"   - {col}")
            
            # Standardize column names
            df_processed = self._standardize_kaggle(df)
            
            logger.info(f"\n✅ Processed Kaggle data:")
            logger.info(f"   Records: {len(df_processed)}")
            logger.info(f"   Columns: {list(df_processed.columns)}")
            
            return df_processed
        
        except FileNotFoundError:
            logger.error(f"❌ File not found: {filepath}")
            return None
        except Exception as e:
            logger.error(f"❌ Error loading Kaggle data: {e}")
            return None
    
    def _standardize_kaggle(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize Kaggle dataset columns for Fair-XAI framework
        
        Expected columns (may vary):
        - Category (job role)
        - Clean_resume / Resume_text
        - Skills
        - Education
        - Experience
        - (Gender, age estimated from name/context) [may not be present]
        """
        
        df_std = df.copy()
        
        # Standardize column names to lowercase and replace spaces
        df_std.columns = df_std.columns.str.lower().str.replace(' ', '_')
        
        # Column mapping (adjust based on actual Kaggle structure)
        column_mapping = {
            'category': 'job_category',
            'clean_resume': 'clean_text',
            'resume_text': 'resume_text',
            'clean_text': 'clean_text',
            'skills': 'skills',
            'education': 'education',
            'experience': 'experience'
        }
        
        # Rename columns that exist
        for old_col, new_col in column_mapping.items():
            if old_col in df_std.columns and old_col != new_col:
                df_std.rename(columns={old_col: new_col}, inplace=True)
        
        # Add ID if missing
        if 'id' not in df_std.columns:
            df_std.insert(0, 'id', range(len(df_std)))
        
        # Estimate gender from name if possible (for analysis)
        if 'gender' not in df_std.columns and any(col in df_std.columns for col in ['name', 'Name']):
            logger.warning("⚠️  Gender not found in Kaggle data - cannot compute gender fairness metrics")
            logger.info("    Tip: Use synthetic data for gender fairness analysis")
            df_std['gender'] = 'Unknown'
        
        # Add experience level if missing (estimate if years_experience present)
        if 'experience_level' not in df_std.columns:
            if 'experience' in df_std.columns or 'years_experience' in df_std.columns:
                # Try to extract years
                exp_col = 'experience' if 'experience' in df_std.columns else 'years_experience'
                try:
                    df_std['years_experience'] = pd.to_numeric(df_std[exp_col], errors='coerce')
                    df_std['experience_level'] = pd.cut(
                        df_std['years_experience'],
                        bins=[0, 2, 7, 100],
                        labels=['entry', 'mid', 'senior']
                    )
                except:
                    df_std['experience_level'] = 'unknown'
            else:
                df_std['experience_level'] = 'unknown'
        
        # Add prediction column if missing
        if 'prediction' not in df_std.columns:
            logger.warning("⚠️  'prediction' column not found")
            logger.info("    You need to add binary predictions (0/1) for fairness analysis")
            df_std['prediction'] = np.random.randint(0, 2, len(df_std))  # Placeholder
        
        if 'prediction_score' not in df_std.columns:
            df_std['prediction_score'] = np.random.uniform(0, 1, len(df_std))  # Placeholder
        
        # Get only columns that exist
        required_cols = ['id', 'job_category', 'gender', 'experience_level', 
                        'prediction', 'prediction_score', 'clean_text']
        return_cols = [col for col in required_cols if col in df_std.columns]
        
        # If missing any critical columns, add them
        if 'clean_text' not in df_std.columns:
            # Try to use resume_text if available
            if 'resume_text' in df_std.columns:
                df_std['clean_text'] = df_std['resume_text']
            else:
                df_std['clean_text'] = 'N/A'
                
        return_cols = [col for col in required_cols if col in df_std.columns]
        return df_std[return_cols]
    
    # ============================================================================
    # SYNTHETIC DATASET (CONTROLLED)
    # ============================================================================
    
    def load_synthetic_data(self, filename: str = "Resume_Dataset_600_Balanced (1).xlsx") -> pd.DataFrame:
        """
        Load synthetic balanced resume dataset (600 resumes)
        
        Args:
            filename: XLSX filename in Downloads folder
        
        Returns:
            Processed DataFrame with standardized columns
        """
        
        filepath = Path(self.downloads_dir) / filename
        
        logger.info(f"\n{'='*80}")
        logger.info(f"LOADING SYNTHETIC DATASET (BALANCED 600)")
        logger.info(f"{'='*80}")
        logger.info(f"📂 Loading from: {filepath}")
        
        try:
            df = pd.read_excel(filepath)
            logger.info(f"✅ Loaded: {len(df)} records, {len(df.columns)} columns")
            
            # Display available columns
            logger.info(f"\n📊 Columns found:")
            for col in df.columns:
                logger.info(f"   - {col}")
            
            # Standardize column names
            df_processed = self._standardize_synthetic(df)
            
            logger.info(f"\n✅ Processed Synthetic data:")
            logger.info(f"   Records: {len(df_processed)}")
            logger.info(f"   Columns: {list(df_processed.columns)}")
            
            # Show distribution
            logger.info(f"\n📊 Distribution:")
            if 'gender' in df_processed.columns:
                logger.info(f"   Gender: {df_processed['gender'].value_counts().to_dict()}")
            if 'experience_level' in df_processed.columns:
                logger.info(f"   Experience: {df_processed['experience_level'].value_counts().to_dict()}")
            
            return df_processed
        
        except FileNotFoundError:
            logger.error(f"❌ File not found: {filepath}")
            return None
        except Exception as e:
            logger.error(f"❌ Error loading synthetic data: {e}")
            return None
    
    def _standardize_synthetic(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize synthetic dataset columns
        
        Expected columns (from generated balanced dataset):
        - ID or index
        - Gender (Male/Female)
        - College_Tier (education level)
        - Skills_Level (skills count)
        - Experience (years or level)
        - Label (prediction/target)
        - Test_Purpose (optional)
        """
        
        df_std = df.copy()
        
        # Standardize column names (case-insensitive)
        df_std.columns = df_std.columns.str.lower().str.replace(' ', '_')
        
        # Column mapping - map from standard names to possible actual column names
        possible_mappings = {
            'gender': ['gender', 'gen', 'sex'],
            'experience_level': ['experience_level', 'exp_level', 'level', 'tier', 'college_tier'],
            'years_experience': ['years_experience', 'years_exp', 'experience_years', 'experience'],
            'education': ['education', 'edu', 'degree', 'college_tier'],
            'skills': ['skills', 'skill_count', 'num_skills', 'skills_level'],
            'job_category': ['job_category', 'category', 'role', 'job_title', 'title'],
            'prediction': ['prediction', 'label', 'target', 'output', 'result'],
            'id': ['id', 'resume_id', 'index']
        }
        
        # Rename to standard columns
        for standard_col, possible_cols in possible_mappings.items():
            for possible_col in possible_cols:
                if possible_col in df_std.columns and standard_col not in df_std.columns:
                    df_std.rename(columns={possible_col: standard_col}, inplace=True)
                    break
        
        # Add ID if missing
        if 'id' not in df_std.columns:
            df_std.insert(0, 'id', range(len(df_std)))
        
        # Ensure experience_level exists (use education or experience as fallback)
        if 'experience_level' not in df_std.columns:
            if 'education' in df_std.columns:
                df_std['experience_level'] = df_std['education']
            else:
                df_std['experience_level'] = 'unknown'
        
        # Add years_experience if missing
        if 'years_experience' not in df_std.columns:
            if 'experience' in df_std.columns:
                try:
                    df_std['years_experience'] = pd.to_numeric(df_std['experience'], errors='coerce').fillna(0)
                except:
                    df_std['years_experience'] = 0
            else:
                df_std['years_experience'] = 0
        
        # Add prediction if missing (use label or create heuristic)
        if 'prediction' not in df_std.columns:
            logger.warning("⚠️  'prediction' column not found")
            # Simple heuristic based on available features
            if 'experience_level' in df_std.columns and 'skills' in df_std.columns:
                try:
                    senior_mask = df_std['experience_level'].astype(str).str.lower().str.contains('senior|high', na=False)
                    high_skills = pd.to_numeric(df_std.get('skills', 0), errors='coerce') > 10
                    df_std['prediction'] = (senior_mask & high_skills).astype(int)
                except:
                    df_std['prediction'] = np.random.randint(0, 2, len(df_std))
            else:
                df_std['prediction'] = np.random.randint(0, 2, len(df_std))
        
        # Ensure prediction is numeric
        df_std['prediction'] = pd.to_numeric(df_std['prediction'], errors='coerce').astype(int)
        
        if 'prediction_score' not in df_std.columns:
            # Convert binary to continuous score with some noise
            df_std['prediction_score'] = df_std['prediction'].astype(float) + np.random.normal(0, 0.1, len(df_std))
            df_std['prediction_score'] = df_std['prediction_score'].clip(0, 1)
        
        # Generate clean_text if missing
        if 'clean_text' not in df_std.columns:
            df_std['clean_text'] = 'synthetic resume text'
        
        # Return all available key columns
        return_cols = []
        for col in ['id', 'gender', 'experience_level', 'years_experience',
                   'prediction', 'prediction_score', 'clean_text']:
            if col in df_std.columns:
                return_cols.append(col)
        
        return df_std[return_cols]
    
    # ============================================================================
    # SAVE & EXPORT
    # ============================================================================
    
    def save_processed_data(self, df: pd.DataFrame, dataset_name: str, 
                           format: str = 'csv'):
        """
        Save processed dataset
        
        Args:
            df: Processed DataFrame
            dataset_name: 'kaggle' or 'synthetic'
            format: 'csv' or 'json'
        """
        
        if format == 'csv':
            filename = f"fairxai_{dataset_name}_processed.csv"
            filepath = Path(self.project_dir) / filename
            df.to_csv(filepath, index=False)
            logger.info(f"✅ Saved: {filepath}")
        
        elif format == 'json':
            filename = f"fairxai_{dataset_name}_processed.json"
            filepath = Path(self.project_dir) / filename
            df.to_json(filepath, orient='records', indent=2)
            logger.info(f"✅ Saved: {filepath}")
    
    # ============================================================================
    # MERGE & COMPARATIVE ANALYSIS
    # ============================================================================
    
    def merge_datasets(self, kaggle_df: pd.DataFrame, 
                      synthetic_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge Kaggle + Synthetic datasets for comparative analysis
        
        Args:
            kaggle_df: Processed Kaggle data
            synthetic_df: Processed synthetic data
        
        Returns:
            Combined DataFrame with source indicator
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"MERGING DATASETS FOR COMPARATIVE ANALYSIS")
        logger.info(f"{'='*80}")
        
        # Add source column
        kaggle_df['data_source'] = 'Real (Kaggle)'
        synthetic_df['data_source'] = 'Synthetic (Controlled)'
        
        # Merge
        combined = pd.concat([kaggle_df, synthetic_df], ignore_index=True)
        
        logger.info(f"✅ Combined dataset:")
        logger.info(f"   Total records: {len(combined)}")
        logger.info(f"   Kaggle: {len(kaggle_df)}")
        logger.info(f"   Synthetic: {len(synthetic_df)}")
        logger.info(f"\n   Source distribution:")
        for source, count in combined['data_source'].value_counts().items():
            logger.info(f"   {source}: {count}")
        
        return combined
    
    def get_fairness_analysis_config(self) -> Dict:
        """
        Get recommended configuration for fairness analysis based on loaded data
        
        Returns:
            Dictionary with analysis configuration
        """
        
        config = {
            'kaggle': {
                'attributes_to_analyze': {
                    # Gender might not be available, use as fallback
                    # 'gender': ('Male', 'Female')  # Commented - may not exist
                },
                'fairness_note': '⚠️  Kaggle data may lack gender information. '
                               'Use synthetic dataset for gender fairness testing.',
                'use_for': 'Real-world validation of fairness metrics'
            },
            'synthetic': {
                'attributes_to_analyze': {
                    'gender': ('Male', 'Female'),
                    'experience_level': ('senior', 'entry')
                },
                'fairness_note': '✅ Synthetic data has balanced gender + experience',
                'use_for': 'Controlled fairness experiments'
            },
            'combined': {
                'purpose': 'Compare fairness metrics between real and synthetic data',
                'note': 'Validate that findings generalize'
            }
        }
        
        return config


class FairXAIDataExplorer:
    """
    Explore loaded data and understand structure for Fair-XAI framework
    """
    
    @staticmethod
    def explore_dataset(df: pd.DataFrame, dataset_name: str) -> Dict:
        """
        Comprehensive data exploration
        
        Args:
            df: DataFrame to explore
            dataset_name: Name for logging
        
        Returns:
            Dictionary with exploration results
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"EXPLORING {dataset_name.upper()}")
        logger.info(f"{'='*80}")
        
        exploration = {
            'name': dataset_name,
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'statistics': {}
        }
        
        # Basic statistics
        logger.info(f"\n📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        
        logger.info(f"\n📋 Columns & Types:")
        for col, dtype in df.dtypes.items():
            missing = df[col].isnull().sum()
            missing_pct = 100 * missing / len(df)
            logger.info(f"   {col:<20} ({dtype}) - {missing} missing ({missing_pct:.1f}%)")
        
        # Distribution of key columns
        logger.info(f"\n📈 Key Distributions:")
        
        for col in ['gender', 'experience_level', 'prediction', 'data_source']:
            if col in df.columns:
                dist = df[col].value_counts().to_dict()
                logger.info(f"\n   {col}:")
                for val, count in sorted(dist.items(), key=lambda x: x[1], reverse=True):
                    pct = 100 * count / len(df)
                    logger.info(f"      {val}: {count} ({pct:.1f}%)")
        
        # Numeric statistics
        logger.info(f"\n📊 Numeric Statistics:")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            logger.info(f"   {col}: mean={df[col].mean():.2f}, "
                       f"std={df[col].std():.2f}, "
                       f"min={df[col].min():.2f}, max={df[col].max():.2f}")
        
        return exploration


# ============================================================================
# MAIN: DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    
    logger.info("\n" + "="*100)
    logger.info("FAIR-XAI DATA LOADER - DEMONSTRATION")
    logger.info("="*100)
    
    # Initialize loader
    loader = FairXAIDataLoader()
    
    # Load both datasets
    logger.info("\n" + "="*100)
    logger.info("STEP 1: LOAD KAGGLE DATA (REAL)")
    logger.info("="*100)
    
    kaggle_df = loader.load_kaggle_data()
    if kaggle_df is not None:
        explorer = FairXAIDataExplorer()
        explorer.explore_dataset(kaggle_df, "Kaggle Data")
        loader.save_processed_data(kaggle_df, 'kaggle', format='csv')
    
    # Load synthetic
    logger.info("\n" + "="*100)
    logger.info("STEP 2: LOAD SYNTHETIC DATA (CONTROLLED)")
    logger.info("="*100)
    
    synthetic_df = loader.load_synthetic_data()
    if synthetic_df is not None:
        explorer = FairXAIDataExplorer()
        explorer.explore_dataset(synthetic_df, "Synthetic Data")
        loader.save_processed_data(synthetic_df, 'synthetic', format='csv')
    
    # Merge for comparison
    if kaggle_df is not None and synthetic_df is not None:
        logger.info("\n" + "="*100)
        logger.info("STEP 3: MERGE FOR COMPARATIVE ANALYSIS")
        logger.info("="*100)
        
        combined_df = loader.merge_datasets(kaggle_df, synthetic_df)
        explorer.explore_dataset(combined_df, "Combined Data")
        loader.save_processed_data(combined_df, 'combined', format='csv')
    
    # Show configuration
    logger.info("\n" + "="*100)
    logger.info("FAIRNESS ANALYSIS CONFIGURATION")
    logger.info("="*100)
    
    config = loader.get_fairness_analysis_config()
    print(json.dumps(config, indent=2))
    
    logger.info("\n✅ Data loading complete!")
    logger.info("\nNext steps:")
    logger.info("1. Use fairxai_kaggle_processed.csv or fairxai_synthetic_processed.csv")
    logger.info("2. Run fairxai_auditing_pipeline.py with processed data")
    logger.info("3. Compare fairness metrics between real and synthetic")
